"""风险评估Agent:用 LangGraph create_react_agent + response_format 实现 ReAct 循环。

面试要点:
1. create_react_agent 实现真正的 ReAct 循环:LLM → 工具 → 观察 → 再推理 → ... → 结论。
2. response_format 直接输出 RiskAssessment,避免 ReAct 后额外的 LLM 调用。
3. 区别于 LCEL:LCEL 是线性管道,LangGraph 是有状态图(可循环/分支)。
4. 规则引擎的风险用 risk_type+drug 做去重键,避免 LLM 改写描述导致重复。
"""
import logging
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema
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
    # ---- 可解释性字段（系统回填，不是 LLM 的输出契约）----
    # 为什么用 SkipJsonSchema：这个类是 ReAct 的 response_format，
    # 不排除的话模型会被要求输出这两个系统字段（它根本判断不了），白耗 token 还可能乱填。
    # 排除后 model_json_schema() 里只有 overall_risk/risks，但 model_dump() 仍带这两个字段。
    floor_applied: SkipJsonSchema[bool] = Field(
        default=False,
        description="最终等级是否由规则/图谱地板决定（而非 LLM 自己的判断）：抬升、或 LLM 未给出可解析等级时为 True",
    )
    llm_original_risk: SkipJsonSchema[str] = Field(
        default="",
        description="地板生效前 LLM 自己给出的等级；\"\"=LLM 未参与，\"unknown\"=LLM 未给出可解析等级",
    )


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


def _deterministic_risks(interactions, contraindications, rule_risks) -> list[RiskItem]:
    """图谱交互 + 禁忌症 + 规则 → RiskItem 列表（不依赖 LLM）。"""
    items: list[RiskItem] = []
    for it in interactions or []:
        items.append(RiskItem(
            drug=f"{it.get('drug_a','')}+{it.get('drug_b','')}",
            risk_type="interaction",
            severity=it.get("severity", "high"),
            description=it.get("mechanism", "药物相互作用"),
            source="graph",
            suggestion="评估是否需调整方案或加强监测",
        ))
    for ct in contraindications or []:
        items.append(RiskItem(
            drug=ct.get("drug", ""),
            risk_type="contraindication",
            severity=ct.get("severity", "high"),
            description=f"{ct.get('condition','')}: {ct.get('contraindication','')}",
            source="graph",
            suggestion="核对禁忌，必要时停用或换药",
        ))
    for rr in rule_risks or []:
        items.append(RiskItem(
            drug=rr.get("drug", ""),
            risk_type=rr.get("risk_type", "rule"),
            severity=rr.get("severity", "high"),
            description=rr.get("risk", ""),
            source="rule",
            suggestion=rr.get("suggestion", ""),
        ))
    return items


def _max_severity_rank(items: list[RiskItem], default: str = "safe") -> str:
    rank = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    best, best_r = default, rank.get(default, 0)
    for r in items:
        cur = rank.get(r.severity, 0)
        if cur > best_r:
            best, best_r = r.severity, cur
    return best


def _normalize_risk(level: str) -> str:
    _RISK_NORMALIZE = {
        "critical": "critical", "critial": "critical", "危急": "critical", "严重": "critical",
        "high": "high", "高风险": "high", "重要": "high",
        "medium": "medium", "moderate": "medium", "中等": "medium", "中风险": "medium",
        "low": "low", "低": "low", "低风险": "low",
        "safe": "safe", "安全": "safe", "not_safe": "high", "not safe": "high",
        "unsafe": "high", "不安全": "high", "unknown": "unknown",
    }
    raw = (level or "unknown").strip().lower()
    return _RISK_NORMALIZE.get(raw, "unknown")


def _llm_react_assess(context: str) -> RiskAssessment | None:
    """ReAct 工具循环评估；失败返回 None。"""
    try:
        llm = get_llm()
        react_agent = create_react_agent(
            model=llm,
            tools=RISK_TOOLS,
            state_modifier=SYSTEM_PROMPT,
            response_format=RiskAssessment,
        )
        react_result = react_agent.invoke(
            {"messages": [HumanMessage(content=f"请评估以下处方的安全性:\n\n{context}")]},
            config={"recursion_limit": 50},
        )
        result = react_result.get("structured_response")
        if isinstance(result, RiskAssessment):
            return result
        if result is not None:
            return RiskAssessment.model_validate(result)
    except Exception as e:
        logger.error(f"ReAct 风险评估失败: {e}")
    return None


def _llm_semantic_assess(context: str) -> RiskAssessment | None:
    """单次 structured output 语义评估（默认路径，延迟可控）。"""
    try:
        from app.agents.semantic_assess import assess_risk_llm_once
        llm_out = assess_risk_llm_once(context)
        risks = [
            RiskItem(
                drug=r.drug, risk_type=r.risk_type or "llm",
                severity=_normalize_risk(r.severity) if _normalize_risk(r.severity) != "unknown" else "medium",
                description=r.description, source="llm", suggestion=r.suggestion,
            )
            for r in llm_out.risks
        ]
        return RiskAssessment(
            overall_risk=_normalize_risk(llm_out.overall_risk),
            risks=risks,
            summary=llm_out.summary or "",
        )
    except Exception as e:
        logger.error(f"语义风险评估失败: {e}")
        return None


def assess_risk(
    interactions: list[dict],
    contraindications: list[dict],
    rule_risks: list[dict],
    patient: dict,
    drugs: list[dict],
) -> RiskAssessment:
    """综合风险评估：确定性地板 + 可选 LLM。

    RISK_MODE:
      - semantic（默认）: 单次 structured output，延迟可控
      - react: ReAct 工具循环（慢，演示用）；失败自动降级 semantic
      - rules: 纯图谱+规则，不调 LLM

    无论 LLM 输出什么，overall_risk 不得低于图谱/规则最高 severity。
    """
    from app.config import settings

    # ---- 确定性地板 ----
    det_items = _deterministic_risks(interactions, contraindications, rule_risks)
    det_floor = _max_severity_rank(det_items, default="safe")

    context_parts = [
        "## 患者信息",
        f"- 年龄: {patient.get('age', '未知')}",
        f"- 性别: {patient.get('gender', '未知')}",
        f"- 诊断: {patient.get('conditions', [])}",
        f"- 过敏史: {patient.get('allergies', [])}",
        f"- 肝功能: {patient.get('liver_function', '正常')}",
        f"- 肾功能: {patient.get('renal_function', '正常')}",
        f"- 孕期: {patient.get('pregnancy', '否')}",
        "\n## 处方药物",
    ]
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

    mode = (getattr(settings, "risk_mode", "semantic") or "semantic").strip().lower()
    result: RiskAssessment | None = None
    if mode == "react":
        result = _llm_react_assess(context)
        if result is None:
            logger.warning("ReAct 评估失败，降级 semantic")
            result = _llm_semantic_assess(context)
    elif mode == "rules":
        result = None
    else:
        result = _llm_semantic_assess(context)

    if result is None:
        result = RiskAssessment(
            overall_risk=det_floor if det_floor != "safe" else "safe",
            risks=[],
            summary="仅图谱+规则（无 LLM 或 LLM 不可用）" if mode == "rules" else "LLM 不可用，仅图谱+规则",
        )

    result.overall_risk = _normalize_risk(result.overall_risk)
    # 先把 LLM 自己的判断记下来：后面地板抬升要拿它做对比，并透出给接口/界面
    llm_judgement = result.overall_risk
    if result.overall_risk == "unknown":
        result.overall_risk = det_floor

    # 合并确定性风险（risk_type+drug 去重）
    existing_keys = {(r.risk_type, r.drug) for r in result.risks}
    for item in det_items:
        key = (item.risk_type, item.drug)
        if key not in existing_keys:
            result.risks.append(item)
            existing_keys.add(key)

    # 规则/图谱地板：不得被 LLM 降级
    # 可解释性：以前这里只有一条 logger.warning —— 只进后端日志，不进接口、不进报告、不进界面，
    # 药师没法分辨「极高危」到底是 LLM 自己判的，还是规则把它从低危强制抬上来的。
    # 现在同一件事同时写进结构化字段，供 API / 前端透出（医疗 AI 的可追溯性要求）。
    rank = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    if rank.get(det_floor, 0) > rank.get(result.overall_risk, 0):
        logger.warning("确定性地板(%s)高于 LLM(%s)，已抬升", det_floor, llm_judgement)
        result.overall_risk = det_floor
        result.floor_applied = True
        result.llm_original_risk = llm_judgement
    elif llm_judgement == "unknown":
        # LLM 参与了、但没给出可解析的等级；最终等级实际由规则/图谱决定，同样属于"不是 LLM 判的"
        logger.warning("LLM 未给出可解析等级，采用规则/图谱判定(%s)", det_floor)
        result.floor_applied = True
        result.llm_original_risk = "unknown"

    return result
