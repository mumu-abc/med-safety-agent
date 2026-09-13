"""药物交互检测Agent:用 LangGraph create_react_agent 实现 ReAct 循环。

面试要点:
1. 统一用 create_react_agent,三个 Agent 架构一致。
2. ReAct 循环:LLM 自主决定调哪些工具、调几轮,直到信息充足。
3. 工具结果直接从 ReAct 消息历史中提取,不做重复查询。
4. LLM 的 final_analysis 也被消费,作为补充分析。
"""
import json
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.prebuilt import create_react_agent
from app.llm import get_llm
from app.graph.drug_graph import (
    get_drug_by_name, find_interactions, find_contraindications
)


# ---- Tools ----

@tool
def lookup_drug(name: str) -> dict:
    """根据药品名称查找药物详细信息(包括分类、禁忌症、副作用、代谢途径)。
    输入:药品名称,如'华法林'、'阿司匹林'。"""
    drug = get_drug_by_name(name)
    if drug:
        return {
            "found": True, "name": drug.get("name"),
            "category": drug.get("category"),
            "contraindications": drug.get("contraindications", []),
            "side_effects": drug.get("side_effects", []),
            "metabolism": drug.get("metabolism", ""),
        }
    return {"found": False, "name": name}


@tool
def check_all_pairs(drug_names: list[str]) -> list[dict]:
    """检查多个药物之间的所有两两相互作用。
    输入:药品名称列表,如['华法林', '阿司匹林']。"""
    drug_ids = []
    for name in drug_names:
        d = get_drug_by_name(name)
        if d:
            drug_ids.append(d["id"])
    if len(drug_ids) < 2:
        return []
    return find_interactions(drug_ids)


@tool
def check_patient_contraindications(drug_name: str, conditions: list[str]) -> list[dict]:
    """检查药物是否与患者的疾病/状况存在禁忌。
    输入:药品名称 + 患者状况列表(如['孕妇', '肝功能不全'])。"""
    drug = get_drug_by_name(drug_name)
    if not drug:
        return []
    return find_contraindications(drug["id"], conditions)


INTERACTION_TOOLS = [lookup_drug, check_all_pairs, check_patient_contraindications]

SYSTEM_PROMPT = """你是药物交互检测专家。使用工具检查药物相互作用和禁忌症。

工具:
- lookup_drug: 查询药品详情
- check_all_pairs: 检查所有药物对的相互作用
- check_patient_contraindications: 检查药物禁忌症

工作流程:
1. 先用 check_all_pairs 检查所有药物的相互作用
2. 如果有患者状况,用 check_patient_contraindications 检查禁忌症
3. 对关键药物用 lookup_drug 获取详细信息
4. 给出最终分析总结"""


def _build_react_agent():
    """创建 LangGraph ReAct Agent。"""
    llm = get_llm()
    # langgraph 0.2.x 起不再接受 prompt=,应使用 state_modifier=
    return create_react_agent(model=llm, tools=INTERACTION_TOOLS, state_modifier=SYSTEM_PROMPT)


def _extract_tool_results(messages: list[BaseMessage]) -> tuple[list[dict], list[dict]]:
    """从 ReAct 消息历史中提取工具返回的交互和禁忌症数据。"""
    all_interactions = []
    all_contras = []

    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            data = json.loads(msg.content)
        except (json.JSONDecodeError, TypeError):
            continue

        # check_all_pairs 返回 list[dict]
        if isinstance(data, list) and data and "drug_a" in data[0]:
            all_interactions.extend(data)
        # check_patient_contraindications 返回 list[dict]
        elif isinstance(data, list) and data and "contraindication" in data[0]:
            all_contras.extend(data)

    return all_interactions, all_contras


def _extract_final_analysis(messages: list[BaseMessage]) -> str:
    """提取 LLM 的最终分析文本。"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return msg.content
    return ""


def detect_interactions(drug_names: list[str], patient_conditions: list[str] | None = None) -> dict:
    """检测药物相互作用与禁忌症。

    默认走确定性图谱直查(毫秒级)。`DETECT_MODE=react` 时先尝试 ReAct,
    失败仍回退图谱——安全关键场景下 LLM 故障不得清空结果。

    历史缺陷:早期默认 ReAct,异常时返回空 interactions,等于图谱也瞎了;
    且在部分国产模型上 tool-calling 循环极慢。现已默认 graph。
    """
    from app.config import settings

    mode = (settings.detect_mode or "graph").strip().lower()
    if mode != "react":
        return _fallback_graph_detect(drug_names, patient_conditions, "图谱直查(默认)")

    input_text = f"处方药物: {', '.join(drug_names)}"
    if patient_conditions:
        input_text += f"\n患者状况: {', '.join(patient_conditions)}"
    input_text += "\n请检查所有药物相互作用和禁忌症。"

    final_analysis = ""
    try:
        react_agent = _build_react_agent()
        react_result = react_agent.invoke(
            {"messages": [HumanMessage(content=input_text)]},
            config={"recursion_limit": 50},
        )
        interactions, contras = _extract_tool_results(react_result["messages"])
        final_analysis = _extract_final_analysis(react_result["messages"])
        if interactions or contras:
            return {
                "interactions": interactions,
                "contraindications": contras,
                "analysis": final_analysis,
            }
        logger.warning("ReAct 未返回工具结果,回退图谱直查")
    except Exception as e:
        logger.error(f"交互检测Agent异常,回退图谱直查: {e}")
        final_analysis = f"⚠️ ReAct失败已降级图谱直查: {type(e).__name__}"

    return _fallback_graph_detect(drug_names, patient_conditions, final_analysis)


def _fallback_graph_detect(drug_names: list[str], patient_conditions: list[str] | None, analysis: str = "") -> dict:
    """确定性图谱查询兜底(不依赖 LLM)。"""
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications

    try:
        build_graph_from_data()
    except Exception:
        pass
    ids = []
    for name in drug_names or []:
        d = get_drug_by_name(name)
        if d:
            ids.append(d["id"])
    interactions = find_interactions(ids) if len(ids) >= 2 else []
    contras = []
    conditions = patient_conditions or []
    for did in ids:
        contras.extend(find_contraindications(did, conditions))
    return {
        "interactions": interactions,
        "contraindications": contras,
        "analysis": analysis or "图谱直查兜底",
    }
