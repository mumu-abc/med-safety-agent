"""Supervisor Agent:多 Agent 编排核心。

真正的 Supervisor 模式:
1. Supervisor 决策节点:inspect 全局状态,动态决定下一步调哪个子 Agent。
2. 循环检测:风险评估结果不明确或高风险但交互数据不足时,自动重跑 detect。
3. 条件路由:根据中间结果决定流程,而非固定边。
4. agent_history 记录完整执行路径 + 路由原因,可追踪调试。

架构:
  parse → supervisor ─→ detect ─┐
               ↑        rules ─┤→ assess ─┐
               │                  │        │
               └── re_detect ←────┘        │
                              recommend ←──┤
                              gen_report ←─┘ → END
"""
import logging
import uuid
import operator
from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.prescription_agent import parse_prescription, Prescription, PatientInfo
from app.agents.interaction_agent import detect_interactions
from app.agents.risk_agent import assess_risk, RiskAssessment
from app.agents.alternative_agent import recommend_alternatives, AlternativeReport
from app.graph.drug_graph import get_drug_by_name
from app.rules.safety_rules import run_all_rules
from app.reporter import generate_report

logger = logging.getLogger(__name__)

MAX_ROUNDS = 3


def _build_supervisor_graph():
    """构建真正的 Supervisor 编排图。

    核心:一个 supervisor 节点作为中央路由器,
    根据当前状态动态决定下一步执行哪个子 Agent。
    """

    from typing import TypedDict

    class MultiAgentState(TypedDict, total=False):
        raw_text: str
        prescription: Prescription
        drug_names: list[str]
        drugs_info: list[dict]
        patient: dict
        interactions: list[dict]
        contraindications: list[dict]
        rule_risks: list[dict]
        risk_assessment: RiskAssessment
        alternatives: AlternativeReport
        report: str
        # Supervisor 追踪 (Annotated 允许并发节点合并写入)
        agent_history: Annotated[list[str], operator.add]
        detect_done: bool
        rules_done: bool
        assess_done: bool
        recommend_done: bool
        redetect_count: int

    # ---- 子 Agent 节点 ----

    def node_parse(state: MultiAgentState) -> dict:
        raw_text = state.get("raw_text", "")
        try:
            prescription = parse_prescription(raw_text)
        except Exception as e:
            logger.error(f"处方解析失败: {e}")
            prescription = Prescription(diagnosis="", drugs=[], patient=PatientInfo())

        drug_names = [d.name for d in prescription.drugs]
        drugs_info = []
        for d in prescription.drugs:
            drug = get_drug_by_name(d.name)
            drugs_info.append(drug if drug else {"name": d.name, "id": d.name})

        patient = {
            "age": prescription.patient.age,
            "gender": prescription.patient.gender,
            "conditions": prescription.patient.conditions,
            "allergies": prescription.patient.allergies,
            "liver_function": prescription.patient.liver_function,
            "renal_function": prescription.patient.renal_function,
            "pregnancy": prescription.patient.pregnancy,
        }

        return {
            "prescription": prescription,
            "drug_names": drug_names,
            "drugs_info": drugs_info,
            "patient": patient,
            "agent_history": ["parse"],
            "detect_done": False,
            "rules_done": False,
            "assess_done": False,
            "recommend_done": False,
            "redetect_count": 0,
            "interactions": [],
            "contraindications": [],
            "rule_risks": [],
        }

    def node_detect(state: MultiAgentState) -> dict:
        drug_names = state.get("drug_names", [])
        patient = state.get("patient", {})
        conditions = patient.get("conditions", [])
        is_redetect = state.get("detect_done", False)

        try:
            result = detect_interactions(drug_names, conditions)
            interactions = result.get("interactions", [])
            contraindications = result.get("contraindications", [])
        except Exception as e:
            logger.error(f"交互检测 Agent 异常: {e}")
            interactions, contraindications = [], []

        tag = "re_detect" if is_redetect else "detect"
        reason = "补充检测(高风险但交互数据不足)" if is_redetect else "首次检测"

        return {
            "interactions": interactions,
            "contraindications": contraindications,
            "agent_history": [f"{tag}:{reason}"],
            "detect_done": True,
            "redetect_count": state.get("redetect_count", 0) + (1 if is_redetect else 0),
        }

    def node_rules(state: MultiAgentState) -> dict:
        drugs_info = state.get("drugs_info", [])
        patient = state.get("patient", {})
        try:
            rule_risks = run_all_rules(drugs_info, patient)
        except Exception as e:
            logger.error(f"规则引擎异常: {e}")
            rule_risks = []

        return {"rule_risks": rule_risks, "agent_history": ["rules"], "rules_done": True}

    def node_assess(state: MultiAgentState) -> dict:
        interactions = state.get("interactions", [])
        contraindications = state.get("contraindications", [])
        rule_risks = state.get("rule_risks", [])
        patient = state.get("patient", {})
        drugs_info = state.get("drugs_info", [])

        try:
            risk_assessment = assess_risk(interactions, contraindications, rule_risks, patient, drugs_info)
        except Exception as e:
            logger.error(f"风险评估 Agent 异常: {e}")
            risk_assessment = RiskAssessment(
                overall_risk="unknown", risks=[],
                summary=f"⚠️ 风险评估失败: {type(e).__name__}"
            )

        return {
            "risk_assessment": risk_assessment,
            "agent_history": [f"assess→{risk_assessment.overall_risk}"],
            "assess_done": True,
        }

    def node_recommend(state: MultiAgentState) -> dict:
        risk_assessment = state.get("risk_assessment")
        drug_names = state.get("drug_names", [])
        patient = state.get("patient", {})

        if not risk_assessment:
            return {"alternatives": AlternativeReport(suggestions=[], summary="无风险评估结果")}

        high_risk_drugs = []
        for r in risk_assessment.risks:
            if r.severity in ("critical", "high") and r.risk_type in ("interaction", "contraindication", "rule"):
                high_risk_drugs.append({"name": r.drug, "risk": r.description})

        if not high_risk_drugs:
            return {"alternatives": AlternativeReport(suggestions=[], summary="无高风险药物需要替代")}

        try:
            alternatives = recommend_alternatives(high_risk_drugs, drug_names, patient, risk_assessment)
        except Exception as e:
            logger.error(f"替代方案 Agent 异常: {e}")
            alternatives = AlternativeReport(suggestions=[], summary=f"⚠️ 替代方案推荐失败: {type(e).__name__}")

        sugg_count = len(alternatives.suggestions) if hasattr(alternatives, 'suggestions') else 0
        return {"alternatives": alternatives, "agent_history": [f"recommend→{sugg_count}个替代方案"], "recommend_done": True}

    def node_report(state: MultiAgentState) -> dict:
        try:
            report = generate_report(state)
        except Exception as e:
            logger.error(f"报告生成异常: {e}")
            report = f"报告生成失败: {e}"

        return {"report": report, "agent_history": ["report"]}

    # ---- Supervisor 决策节点(核心) ----

    def supervisor(state: MultiAgentState) -> str:
        """中央路由器:inspect 全局状态,决定下一步。

        决策逻辑:
        1. parse 未完成 → detect(同时 rules 由另一个边触发)
        2. detect/rules 未完成 → 等待
        3. assess 未完成 → assess
        4. assess 完成后:
           a. 高风险 + 交互数据不足 + 未超过重试上限 → re_detect
           b. 高风险 + 交互数据充足 → recommend
           c. 低风险 → gen_report
        5. recommend 完成 → gen_report
        """
        detect_done = state.get("detect_done", False)
        rules_done = state.get("rules_done", False)
        assess_done = state.get("assess_done", False)
        recommend_done = state.get("recommend_done", False)
        redetect_count = state.get("redetect_count", 0)

        # Step 1-2: detect 和 rules 都完成后才能 assess
        if not detect_done or not rules_done:
            if not detect_done:
                return "detect"
            return "rules"

        # Step 3: assess
        if not assess_done:
            return "assess"

        # Step 4: assess 完成,动态决策
        ra = state.get("risk_assessment")
        if ra and ra.overall_risk in ("critical", "high"):
            interactions = state.get("interactions", [])
            rule_risks = state.get("rule_risks", [])
            # 高风险但交互和规则都没查到数据且未超限 → 重跑 detect
            # 如果规则引擎已经触发了风险,说明风险来源是规则而非交互,不需要重跑
            if len(interactions) == 0 and len(rule_risks) == 0 and redetect_count < MAX_ROUNDS:
                # 标记需要重跑 detect(清除 detect_done)
                state["detect_done"] = False
                logger.info(f"🔄 Supervisor: 高风险但交互数据不足({len(interactions)}条),触发补充检测(第{redetect_count+1}轮)")
                return "detect"
            # 交互数据充足或已超限 → recommend
            if not recommend_done:
                return "recommend"

        # Step 5: 低风险或 recommend 完成 → 生成报告
        return "gen_report"

    # ---- 构建图 ----
    graph = StateGraph(MultiAgentState)

    graph.add_node("parse", node_parse)
    graph.add_node("detect", node_detect)
    graph.add_node("rules", node_rules)
    graph.add_node("assess", node_assess)
    graph.add_node("recommend", node_recommend)
    graph.add_node("gen_report", node_report)

    graph.set_entry_point("parse")

    # parse 完成后 → supervisor 决策
    graph.add_edge("parse", "detect")
    graph.add_edge("parse", "rules")

    # 每个子 Agent 完成后 → 回到 supervisor 决策下一步
    graph.add_edge("detect", "assess")
    graph.add_edge("rules", "assess")

    # assess 后由 supervisor 动态路由
    graph.add_conditional_edges(
        "assess",
        supervisor,
        {
            "detect": "detect",      # 重跑检测(循环)
            "rules": "rules",        # 重跑规则(不应触发,兜底)
            "assess": "assess",      # 重跑评估(不应触发)
            "recommend": "recommend",
            "gen_report": "gen_report",
        },
    )

    # recommend 完成后 → gen_report
    graph.add_edge("recommend", "gen_report")

    # gen_report → END
    graph.add_edge("gen_report", END)

    return graph


# ---- 单例 ----
_supervisor_checkpointer = MemorySaver()
_compiled_supervisor = None
_compiled_supervisor_hitl = None
_AUTO_MULTI_THREAD_ID = "auto-multi-review"


class AttrDict(dict):
    """支持属性访问的 dict,兼容 langgraph 不同版本的返回类型。"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")


def get_supervisor_graph():
    global _compiled_supervisor
    if _compiled_supervisor is None:
        _compiled_supervisor = _build_supervisor_graph().compile(checkpointer=_supervisor_checkpointer)
    return _compiled_supervisor


def get_supervisor_graph_hitl():
    global _compiled_supervisor_hitl
    if _compiled_supervisor_hitl is None:
        _compiled_supervisor_hitl = _build_supervisor_graph().compile(
            checkpointer=_supervisor_checkpointer,
            interrupt_before=["recommend"],
        )
    return _compiled_supervisor_hitl


def review_multi_agent(text: str) -> AttrDict:
    """多 Agent 协作审查入口。

    与 review_prescription 的区别:
    1. Supervisor 动态路由:根据中间结果决定下一步
    2. 循环检测:高风险+交互不足时自动重跑 detect
    3. agent_history 记录完整执行路径 + 路由原因
    """
    graph = get_supervisor_graph()
    config = {"configurable": {"thread_id": _AUTO_MULTI_THREAD_ID}, "recursion_limit": 100}
    result = graph.invoke({"raw_text": text}, config=config)
    return AttrDict(result)


def review_multi_agent_hitl(text: str) -> tuple[AttrDict, str, bool]:
    graph = get_supervisor_graph_hitl()
    thread_id = f"hitl-multi-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
    result = graph.invoke({"raw_text": text}, config=config)
    needs_resume = result.get("report") is None
    return AttrDict(result), thread_id, needs_resume


def resume_multi_agent(thread_id: str) -> AttrDict:
    graph = get_supervisor_graph_hitl()
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(None, config=config)
    return AttrDict(result)
