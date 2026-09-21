"""替代方案Agent:用 LangGraph create_react_agent + response_format 实现 ReAct 循环。

设计要点:
1. create_react_agent 的 response_format 参数直接输出结构化结果。
2. 避免了"ReAct 结束后再调一次 structured_output"的额外 LLM 调用。
3. 只在有高风险时触发——条件执行,不浪费资源。
4. 三个 Agent 统一用 create_react_agent,架构一致。
5. Agent 间通信: risk_agent 的 RiskAssessment 结构化输出直接作为本 Agent 的输入上下文。
"""
import logging
from pydantic import BaseModel, Field
from langchain_core.tools import tool

logger = logging.getLogger(__name__)
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from app.llm import get_llm
from app.agents.risk_agent import RiskAssessment
from app.graph.drug_graph import get_drug_by_name, find_alternatives, find_interactions


# ---- Schema ----

class AlternativeDrug(BaseModel):
    """替代药物(P3-28:用 BaseModel 替代裸 dict)。"""
    name: str = Field(description="药物名称")
    category: str = Field(default="", description="药物分类")
    reason: str = Field(default="", description="推荐理由")


class AlternativeSuggestion(BaseModel):
    original_drug: str = Field(default="", description="原药物")
    alternatives: list[AlternativeDrug] = Field(default_factory=list, description="推荐的替代药物")
    reason: str = Field(default="", description="为什么需要替换")


class AlternativeReport(BaseModel):
    suggestions: list[AlternativeSuggestion] = Field(default_factory=list, description="替代建议列表")
    summary: str = Field(default="", description="总结")


# ---- Tools ----

@tool
def get_alternatives_for(drug_name: str, exclude_drugs: list[str]) -> list[dict]:
    """查找某药物的替代药物。
    输入:原药物名称 + 需要排除的药物名称列表。"""
    drug = get_drug_by_name(drug_name)
    if not drug:
        return []
    exclude_ids = []
    for name in exclude_drugs:
        d = get_drug_by_name(name)
        if d:
            exclude_ids.append(d["id"])
    return find_alternatives(drug["id"], exclude_ids)


@tool
def verify_alternative_safety(alternative_name: str, current_drugs: list[str]) -> dict:
    """验证替代药物与当前处方中其他药物是否安全。
    输入:替代药物名称 + 当前处方中其他药物名称列表。"""
    alt = get_drug_by_name(alternative_name)
    if not alt:
        return {"safe": False, "reason": "未找到该药物"}
    all_ids = [alt["id"]]
    for name in current_drugs:
        d = get_drug_by_name(name)
        if d:
            all_ids.append(d["id"])
    interactions = find_interactions(all_ids)
    critical_high = [i for i in interactions if i["severity"] in ("critical", "high")]
    if critical_high:
        return {"safe": False, "reason": f"存在高风险相互作用: {critical_high[0]['drug_a']} + {critical_high[0]['drug_b']}"}
    return {"safe": True, "reason": "未发现高风险相互作用"}


@tool
def get_drug_info(drug_name: str) -> dict:
    """获取药物详细信息(分类、禁忌症、副作用)。"""
    drug = get_drug_by_name(drug_name)
    if drug:
        return {"name": drug.get("name"), "category": drug.get("category"),
                "contraindications": drug.get("contraindications", []),
                "side_effects": drug.get("side_effects", [])}
    return {"found": False, "name": drug_name}


ALT_TOOLS = [get_alternatives_for, verify_alternative_safety, get_drug_info]

SYSTEM_PROMPT = """你是临床药师,为高风险药物推荐安全的替代方案。

工具:
- get_alternatives_for: 查找某药物的替代药物
- verify_alternative_safety: 验证替代药物与其他药物的安全性
- get_drug_info: 获取药物详细信息

工作流程:
1. 先分析风险评估结果,理解每个高风险药物的具体风险类型和严重程度
2. 对每个高风险药物,用 get_alternatives_for 查找替代方案
3. 用 verify_alternative_safety 验证每个替代药物的安全性
4. 用 get_drug_info 获取替代药物的详细信息
5. 给出结构化的替代方案推荐,说明为什么原药有风险、替代药如何规避该风险

用中文输出。"""


def recommend_alternatives(
    high_risk_drugs: list[dict],
    current_drug_names: list[str],
    patient: dict,
    risk_assessment: RiskAssessment | None = None,
) -> AlternativeReport:
    """用 ReAct Agent 推荐替代方案。

    关键:response_format 直接输出 AlternativeReport,避免额外 LLM 调用。
    Agent 间通信: risk_assessment 参数接收 risk_agent 的结构化输出,提供完整风险上下文。
    """
    if not high_risk_drugs:
        return AlternativeReport(suggestions=[], summary="无高风险药物,无需替代")

    input_parts = ["需要替换的高风险药物:"]
    for d in high_risk_drugs:
        input_parts.append(f"- {d.get('name', '')}: {d.get('risk', '')}")
    input_parts.append(f"\n当前处方其他药物: {', '.join(current_drug_names)}")
    input_parts.append(f"\n患者年龄: {patient.get('age', '未知')}, 肝功能: {patient.get('liver_function', '正常')}, 肾功能: {patient.get('renal_function', '正常')}")

    # Agent 间通信: 将 risk_agent 的结构化输出作为上下文传入
    if risk_assessment and hasattr(risk_assessment, 'risks'):
        input_parts.append("\n--- 风险评估详情 (来自风险评估Agent) ---")
        input_parts.append(f"总体风险: {risk_assessment.overall_risk}")
        input_parts.append(f"风险摘要: {risk_assessment.summary}")
        for r in risk_assessment.risks:
            input_parts.append(f"  [{r.severity}] {r.drug} - {r.risk_type}: {r.description}")
            if r.suggestion:
                input_parts.append(f"    建议: {r.suggestion}")
        input_parts.append("--- 请根据以上风险详情推荐替代方案 ---")

    # ReAct Agent with response_format (直接输出结构化结果,省一次 LLM 调用)
    try:
        llm = get_llm()
        react_agent = create_react_agent(
            model=llm,
            tools=ALT_TOOLS,
            state_modifier=SYSTEM_PROMPT,
            response_format=AlternativeReport,
        )

        react_result = react_agent.invoke(
            {"messages": [HumanMessage(content="\n".join(input_parts))]},
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
                structured_llm = llm.with_structured_output(AlternativeReport)
                result = structured_llm.invoke([
                    HumanMessage(content=f"根据以下分析,输出结构化替代方案:\n\n{final_content}"),
                ])
        if result is None:
            return AlternativeReport(suggestions=[], summary="LLM未返回有效结果")
        return result
    except Exception as e:
        logger.error(f"替代方案Agent异常: {e}")
        return AlternativeReport(suggestions=[], summary=f"⚠️ 替代方案推荐失败: {type(e).__name__}")
