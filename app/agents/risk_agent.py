"""风险评估Agent:用 LangGraph create_react_agent + response_format 实现 ReAct 循环。

面试要点:
1. create_react_agent 实现真正的 ReAct 循环:LLM → 工具 → 观察 → 再推理 → ... → 结论。
2. response_format 直接输出 RiskAssessment,避免 ReAct 后额外的 LLM 调用。
3. 区别于 LCEL:LCEL 是线性管道,LangGraph 是有状态图(可循环/分支)。
4. 规则引擎的风险用 risk_type+drug 做去重键,避免 LLM 改写描述导致重复。
"""
import logging
from pydantic import BaseModel, Field
from langchain_core.tools import tool

logger = logging.getLogger(__name__)
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from app.llm import get_llm
from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications


# ---- Tools ----

@tool
def query_drug_details(drug_name: str) -> dict:
    """查询药物的详细信息(代谢途径、禁忌症、副作用)。
    输入:药品名称,如'华法林'、'阿司匹林'。"""
    drug = get_drug_by_name(drug_name)
    if drug:
        return {"name": drug.get("name"), "category": drug.get("category"),
                "contraindications": drug.get("contraindications", []),
                "side_effects": drug.get("side_effects", []),
                "metabolism": drug.get("metabolism", "")}
    return {"found": False, "name": drug_name}


@tool
def query_interaction_detail(drug_a: str, drug_b: str) -> dict:
    """查询两个药物之间的详细相互作用信息。
    输入:两个药品名称。"""
    a = get_drug_by_name(drug_a)
    b = get_drug_by_name(drug_b)
    if not a or not b:
        return {"found": False}
    interactions = find_interactions([a["id"], b["id"]])
    return {"found": bool(interactions), "interactions": interactions}


@tool
def query_metabolism_conflicts(drug_names: list[str]) -> list[dict]:
    """检查多个药物是否存在代谢途径冲突(如都经CYP3A4代谢)。
    输入:药品名称列表。"""
    drugs = []
    for name in drug_names:
        d = get_drug_by_name(name)
        if d:
            drugs.append(d)
    metabolism_map: dict[str, list[str]] = {}
    for d in drugs:
        met = d.get("metabolism", "")
        if met:
            for enzyme in met.split("/"):
                enzyme = enzyme.strip()
                if enzyme and enzyme not in ("肾脏排泄", "肝脏代谢", "不吸收", "不代谢"):
                    metabolism_map.setdefault(enzyme, []).append(d.get("name", ""))
    conflicts = []
    for enzyme, drug_list in metabolism_map.items():
        if len(drug_list) >= 2:
            conflicts.append({"enzyme": enzyme, "drugs": drug_list,
                              "risk": f"多药竞争{enzyme}代谢,可能互相影响血药浓度"})
    return conflicts


# 药理学通路映射:不同 category 但同属一个作用通路
PHARMACOLOGICAL_PATHWAYS = {
    "RAAS阻断": {"ACEI", "ARB"},
    "β受体阻断": {"β受体阻滞剂", "β受体阻滞剂(选择性)"},
    "他汀类": {"HMG-CoA还原酶抑制剂", "他汀类"},
    "利尿剂": {"袢利尿剂", "噻嗪类利尿剂", "保钾利尿剂"},
    "抗血小板": {"抗血小板药", "P2Y12抑制剂"},
    "NSAIDs": {"NSAIDs", "COX-2抑制剂"},
}


@tool
def query_pharmacological_overlap(drug_names: list[str]) -> list[dict]:
    """检查多个药物是否存在药理学通路重复(如ACEI+ARB都是RAAS阻断剂)。
    输入:药品名称列表。
    返回:重复通路列表,每项包含通路名称和涉及的药物。"""
    drugs = []
    for name in drug_names:
        d = get_drug_by_name(name)
        if d:
            drugs.append({"name": name, "category": d.get("category", "")})

    overlaps = []
    for pathway, categories in PHARMACOLOGICAL_PATHWAYS.items():
        matched = [d for d in drugs if d["category"] in categories]
        if len(matched) >= 2:
            overlaps.append({
                "pathway": pathway,
                "drugs": [d["name"] for d in matched],
                "categories": [d["category"] for d in matched],
                "risk": f"同时使用多个{pathway}药物,属于重复用药,增加不良反应风险",
            })
    return overlaps


RISK_TOOLS = [query_drug_details, query_interaction_detail, query_metabolism_conflicts, query_pharmacological_overlap]


# ---- Schema ----

class RiskItem(BaseModel):
    drug: str = Field(default="", description="涉及的药物")
    risk_type: str = Field(default="rule", description="风险类型: interaction/contraindication/age/pregnancy/renal/hepatic/metabolism/rule")
    severity: str = Field(default="medium", description="严重程度: critical/high/medium/low")
    description: str = Field(default="", description="风险描述")
    source: str = Field(default="", description="来源: rule(规则引擎) / llm(LLM分析)")
    suggestion: str = Field(default="", description="处理建议")


class RiskAssessment(BaseModel):
    overall_risk: str = Field(default="unknown", description="总体风险等级: critical/high/medium/low/safe")
    risks: list[RiskItem] = Field(default_factory=list, description="风险列表")
    summary: str = Field(default="", description="综合评估摘要")


# ---- LangGraph ReAct Agent ----

SYSTEM_PROMPT = """你是资深临床药师,负责评估用药安全性。

你可以使用以下工具查询药物信息:
- query_drug_details: 查询药物详情(代谢途径、禁忌症、副作用)
- query_interaction_detail: 查询两个药物之间的相互作用
- query_metabolism_conflicts: 检查多药代谢途径冲突
- query_pharmacological_overlap: 检查多药药理学通路重复(如ACEI+ARB同为RAAS阻断剂)

工作流程(ReAct循环):
1. 思考:分析处方中哪些药物需要深入检查
2. 行动:调用工具查询药物信息(必须调用 query_pharmacological_overlap 检查同类药物重复)
3. 观察:分析工具返回的结果
4. 重复:如果需要更多信息,继续调用工具
5. 最终结论:综合所有信息,给出结构化的风险评估

必须调用的工具:
- query_pharmacological_overlap: 对所有处方药物调用此工具,检查是否存在同类药物重复用药
  即使图谱没有检测到相互作用,也必须调用此工具

重要规则:
- 规则引擎已识别的风险必须采纳,不得降低其严重程度
- 如果发现代谢途径冲突,必须报告
- 用中文输出

风险校准(重要):
- 如果图谱没有检测到相互作用、规则引擎没有触发、处方中的药物组合合理,overall_risk 应为 "safe"
- 不要因为"药物都有副作用"就报告风险。所有药物都有副作用,只有在特定组合或特定患者条件下才有临床意义的风险
- "safe" 意味着:该处方在当前患者条件下没有需要干预的安全问题
- 只有在以下情况才提升风险等级:
  * critical: 有严重相互作用或绝对禁忌症,可能导致生命危险(如华法林+抗血小板药联用、华法林+NSAIDs联用)
  * high: 有重要相互作用需要调整方案,或单一药物绝对禁忌于该患者(如孕妇使用他汀类、儿童使用氟喹诺酮)
  * medium: 有潜在风险但可以监测下继续使用(如同类药物重复用药、可通过服药时间间隔解决的吸收干扰)
  * low: 有轻微注意点但不影响处方

常见安全组合(不应报告为风险):
- PPI + 促胃动力药(如奥美拉唑+莫沙必利):标准胃炎治疗方案
- 降压药 + 不同类降压药合理联用(如氨氯地平+缬沙坦)
- 降糖药 + 不同类降糖药联用(如二甲双胍+阿卡波糖)
- 通过调整服药时间可解决的吸收相互作用(如左甲状腺素+碳酸钙,间隔4小时服用即可)

风险升级规则:
- 两种及以上抗栓/抗凝药物联用(华法林+阿司匹林/氯吡格雷/NSAIDs)应判为 critical
- 单一药物禁忌于特定患者(孕妇/儿童)应判为 high,不应升级到 critical
- 两个禁忌症叠加但不构成生命危险时仍为 high,不应自动升级到 critical

你的独特能力(规则和图谱无法做到的):
- 识别同类药物重复用药(如同时用两种 ACEI 或两种 ARB)
- 评估药物与患者疾病的整体匹配性(不仅是禁忌症列表中的)
- 判断剂量合理性(结合患者年龄、肝肾功能)
- 你发现的风险,source 字段填 "llm"""


def assess_risk(
    interactions: list[dict],
    contraindications: list[dict],
    rule_risks: list[dict],
    patient: dict,
    drugs: list[dict],
) -> RiskAssessment:
    """用 ReAct Agent + response_format 进行综合风险评估。

    流程:
    1. 构建上下文
    2. ReAct Agent 自主循环调用工具(response_format 直接输出 RiskAssessment)
    3. 合并规则引擎结果(用 risk_type+drug 去重)
    """
    # ---- 构建上下文 ----
    context_parts = []
    context_parts.append("## 患者信息")
    context_parts.append(f"- 年龄: {patient.get('age', '未知')}")
    context_parts.append(f"- 性别: {patient.get('gender', '未知')}")
    context_parts.append(f"- 诊断: {patient.get('conditions', [])}")
    context_parts.append(f"- 过敏史: {patient.get('allergies', [])}")
    context_parts.append(f"- 肝功能: {patient.get('liver_function', '正常')}")
    context_parts.append(f"- 肾功能: {patient.get('renal_function', '正常')}")
    context_parts.append(f"- 孕期: {patient.get('pregnancy', '否')}")

    context_parts.append("\n## 处方药物")
    for d in drugs:
        context_parts.append(f"- {d.get('name', '')} {d.get('dosage', '')} {d.get('frequency', '')}")

    if interactions:
        context_parts.append("\n## 图谱检测到的药物相互作用")
        for it in interactions:
            context_parts.append(f"- {it['drug_a']} + {it['drug_b']}: {it['severity']} — {it['mechanism']}")

    if contraindications:
        context_parts.append("\n## 禁忌症匹配")
        for ct in contraindications:
            context_parts.append(f"- {ct['drug']}: {ct['condition']} → {ct.get('contraindication', '')}")

    if rule_risks:
        context_parts.append("\n## 规则引擎已识别的风险(必须采纳,不得降低)")
        for rr in rule_risks:
            context_parts.append(f"- [{rr['severity']}] {rr['drug']}: {rr['risk']} → {rr.get('suggestion', '')}")

    context = "\n".join(context_parts)

    # ---- ReAct Agent with response_format (直接输出结构化结果,省一次 LLM 调用) ----
    try:
        llm = get_llm()
        react_agent = create_react_agent(
            model=llm,
            tools=RISK_TOOLS,
            prompt=SYSTEM_PROMPT,
            response_format=RiskAssessment,
        )

        react_result = react_agent.invoke(
            {"messages": [HumanMessage(content=f"请评估以下处方的安全性:\n\n{context}")]},
            config={"recursion_limit": 50},
        )

        # response_format 直接输出结构化结果
        result = react_result.get("structured_response")
        if result is None:
            # 兜底:尝试从 messages 提取
            final_content = ""
            messages = react_result.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_call_id"):
                    final_content = msg.content
                    break
            if final_content:
                structured_llm = llm.with_structured_output(RiskAssessment)
                result = structured_llm.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"根据以下分析,输出结构化风险评估:\n\n{final_content}\n\n原始上下文:\n{context}"),
                ])
        if result is None:
            result = RiskAssessment(overall_risk="unknown", risks=[], summary="LLM未返回有效结果")
    except Exception as e:
        logger.error(f"风险评估Agent异常: {e}")
        result = RiskAssessment(overall_risk="unknown", risks=[], summary=f"⚠️ 风险评估失败: {type(e).__name__}")

    # ---- 风险等级归一化(LLM 可能返回非标准值) ----
    _RISK_NORMALIZE = {
        "critical": "critical", "critial": "critical", "危急": "critical", "严重": "critical",
        "high": "high", "高风险": "high", "重要": "high",
        "medium": "medium", "moderate": "medium", "中等": "medium", "中风险": "medium",
        "low": "low", "低": "low", "低风险": "low",
        "safe": "safe", "安全": "safe", "not_safe": "high", "not safe": "high",
        "unsafe": "high", "不安全": "high", "unknown": "unknown",
    }
    raw_risk = result.overall_risk.strip().lower() if result.overall_risk else "unknown"
    result.overall_risk = _RISK_NORMALIZE.get(raw_risk, "unknown")
    if result.overall_risk == "unknown":
        logger.warning(f"LLM 返回非标准风险等级: {raw_risk}")

    # ---- 合并规则引擎结果(P0-5:用 risk_type+drug 去重,而非精确字符串匹配) ----
    # 规则引擎的风险有 risk_type(如"pregnancy"/"hepatic"),用它做去重键
    existing_keys = {(r.risk_type, r.drug) for r in result.risks}
    for rr in rule_risks:
        key = (rr.get("risk_type", "rule"), rr.get("drug", ""))
        if key not in existing_keys:
            result.risks.append(RiskItem(
                drug=rr.get("drug", ""), risk_type=rr.get("risk_type", "rule"),
                severity=rr.get("severity", "high"), description=rr["risk"],
                source="rule", suggestion=rr.get("suggestion", ""),
            ))
    return result
