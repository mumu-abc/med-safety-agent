"""用药安全审查工作流:用 LangGraph StateGraph 编排全流程。

面试要点:
1. 用 LangGraph StateGraph 替代 LCEL | 串联。
2. StateGraph 支持循环、条件分支、状态持久化,LCEL 只能线性管道。
3. 每个节点是独立函数,通过 TypedDict 状态对象传递数据。
4. 条件边:风险评估后根据风险等级决定是否触发替代方案推荐。
5. MemorySaver checkpointer:支持状态持久化和 human-in-the-loop 中断恢复。
6. 流程:parse → detect → rules → assess → (条件) alternatives → report。

支持三种运行模式:
- review_prescription()   — 普通审查,自动跑完全流程
- review_with_hitl()      — HITL 模式,在 recommend 节点前暂停等药师确认
- get_review_graph()      — 返回图实例,供 SSE 流式调用 graph.stream()
"""
import logging
import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agents.prescription_agent import parse_prescription, Prescription
from app.agents.interaction_agent import detect_interactions
from app.rules.safety_rules import run_all_rules
from app.agents.risk_agent import assess_risk, RiskAssessment
from app.agents.alternative_agent import recommend_alternatives, AlternativeReport
from app.graph.drug_graph import get_drug_by_name
from app.reporter import generate_report

logger = logging.getLogger(__name__)


class AttrDict(dict):
    """支持属性访问的 dict,兼容 langgraph 不同版本的返回类型。"""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")


# ---- State 定义 ----

class ReviewState(TypedDict, total=False):
    """贯穿整个图的状态对象。"""
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


# ---- 节点函数 ----

def node_parse(state: ReviewState) -> dict:
    """Step 1: 解析处方(with_structured_output)。"""
    try:
        prescription = parse_prescription(state["raw_text"])
    except Exception as e:
        logger.error(f"处方解析失败: {e}")
        # 返回最小可用状态,后续节点仍能运行
        from app.models import PatientInfo
        prescription = Prescription(
            diagnosis="", drugs=[], patient=PatientInfo(),
        )
    drug_names = [d.name for d in prescription.drugs]
    patient = {
        "age": prescription.patient.age,
        "gender": prescription.patient.gender,
        "conditions": prescription.patient.conditions,
        "allergies": prescription.patient.allergies,
        "liver_function": prescription.patient.liver_function,
        "renal_function": prescription.patient.renal_function,
        "pregnancy": prescription.patient.pregnancy,
    }
    drugs_info = []
    for name in drug_names:
        drug = get_drug_by_name(name)
        drugs_info.append(drug if drug else {"name": name, "id": name})
    return {
        "prescription": prescription,
        "drug_names": drug_names,
        "drugs_info": drugs_info,
        "patient": patient,
    }


def node_detect(state: ReviewState) -> dict:
    """Step 2: 交互检测(ReAct Agent)。"""
    detection = detect_interactions(state["drug_names"], state["patient"].get("conditions"))
    return {
        "interactions": detection["interactions"],
        "contraindications": detection["contraindications"],
    }


def node_rules(state: ReviewState) -> dict:
    """Step 3: 规则引擎(纯硬编码,不经过LLM)。"""
    rule_risks = run_all_rules(state["drugs_info"], state["patient"])
    return {"rule_risks": rule_risks}


def node_assess(state: ReviewState) -> dict:
    """Step 4: 风险评估(ReAct Agent + structured output)。"""
    risk_assessment = assess_risk(
        interactions=state.get("interactions", []),
        contraindications=state.get("contraindications", []),
        rule_risks=state.get("rule_risks", []),
        patient=state["patient"],
        drugs=state["drugs_info"],
    )

    # ---- 安全兜底(安全关键系统的红线) ----
    # 原文非空却一个药都没识别出来 = 解析环节失败了。
    # 此时风险列表是空的,LLM 会顺势给出 safe —— 这是最危险的假阴性:
    # "我解析失败" 被当成了 "这张处方没风险"。
    # 因此必须显式升级为 unknown 并给出人工复核提示。
    if not state.get("drug_names") and (state.get("raw_text") or "").strip():
        from app.agents.risk_agent import RiskItem
        risk_assessment.risks.append(RiskItem(
            drug="(未识别)",
            risk_type="rule",
            severity="medium",
            description="未能从处方文本中识别出任何药品,无法完成审查,请人工复核。"
                        "常见原因:药品名写法不在知识图谱内、文本格式异常、或解析服务异常。",
            source="rule",
            suggestion="请确认处方文本,或改用通用名/标准药品名后重新提交。",
        ))
        if risk_assessment.overall_risk in ("safe", "low", ""):
            risk_assessment.overall_risk = "unknown"
        if not risk_assessment.summary:
            risk_assessment.summary = "解析未获得药品信息,审查未完成,需人工复核。"

    return {"risk_assessment": risk_assessment}


def node_alternatives(state: ReviewState) -> dict:
    """Step 5: 替代方案(ReAct Agent,仅高风险时触发)。"""
    risk_assessment = state.get("risk_assessment")
    if not risk_assessment:
        return {"alternatives": None}

    high_risk_drugs = []
    for r in risk_assessment.risks:
        if r.severity in ("critical", "high") and r.risk_type in ("interaction", "contraindication", "rule"):
            if r.drug not in [d.get("name") for d in high_risk_drugs]:
                high_risk_drugs.append({"name": r.drug, "risk": r.description})

    if high_risk_drugs:
        alternatives = recommend_alternatives(
            high_risk_drugs=high_risk_drugs,
            current_drug_names=state["drug_names"],
            patient=state["patient"],
            risk_assessment=risk_assessment,  # Agent 间通信: risk_agent 输出 → alternative_agent 输入
        )
        return {"alternatives": alternatives}
    return {"alternatives": None}


def node_report(state: ReviewState) -> dict:
    """Step 6: 生成报告。"""
    report = generate_report(state)
    return {"report": report}


# ---- 条件边 ----

def should_recommend_alternatives(state: ReviewState) -> str:
    """根据风险等级决定是否触发替代方案推荐。"""
    risk_assessment = state.get("risk_assessment")
    if not risk_assessment:
        return "report"
    if risk_assessment.overall_risk in ("critical", "high"):
        return "alternatives"
    return "report"


# ---- 构建 StateGraph ----

def _build_graph() -> StateGraph:
    """构建 LangGraph StateGraph。"""
    graph = StateGraph(ReviewState)

    # 添加节点
    graph.add_node("parse", node_parse)
    graph.add_node("detect", node_detect)
    graph.add_node("rules", node_rules)
    graph.add_node("assess", node_assess)
    graph.add_node("recommend", node_alternatives)
    graph.add_node("gen_report", node_report)

    # 设置入口
    graph.set_entry_point("parse")

    # 添加边
    graph.add_edge("parse", "detect")
    graph.add_edge("detect", "rules")
    graph.add_edge("rules", "assess")

    # 条件边:assess 之后根据风险等级决定是否走 alternatives
    graph.add_conditional_edges(
        "assess",
        should_recommend_alternatives,
        {"alternatives": "recommend", "report": "gen_report"},
    )

    graph.add_edge("recommend", "gen_report")
    graph.add_edge("gen_report", END)

    return graph


# 编译图(单例)
# 共享 MemorySaver 单例:自动完成用固定 thread_id(每次覆盖旧状态,HITL 用唯一 thread_id)
_shared_checkpointer = MemorySaver()
_compiled_graph = None
_compiled_graph_hitl = None


def get_review_graph():
    """获取审查图(自动完成模式)。

    有意**不挂 checkpointer**:自动完成模式一次跑完 parse→...→gen_report,
    不需要跨调用保留状态。早期版本给自动模式挂了 MemorySaver + 固定
    thread_id,导致两个问题:
      1. 跨请求状态残留 —— 条件边跳过 `recommend` 节点时,`alternatives`
         字段会保留上一次审查的值,用户 B 拿到用户 A 的换药建议;
      2. 所有审查的 checkpoint 堆在同一个 thread 下,进程内存持续增长。
    需要中断恢复的场景请用 get_review_graph_hitl()。
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph().compile()
    return _compiled_graph


def get_review_graph_hitl():
    """获取带 human-in-the-loop 中断的审查图。

    在 alternatives 节点前中断,等待药师确认后再继续。
    用 checkpointer 持久化状态,支持中断恢复。
    """
    global _compiled_graph_hitl
    if _compiled_graph_hitl is None:
        _compiled_graph_hitl = _build_graph().compile(
            checkpointer=_shared_checkpointer,
            interrupt_before=["recommend"],
        )
    return _compiled_graph_hitl


def review_prescription(text: str) -> ReviewState:
    """完整审查流程入口(自动完成,不中断)。

    内部用 LangGraph StateGraph 编排:
    parse → detect → rules → assess → (条件)alternatives → report
    """
    graph = get_review_graph()
    result = graph.invoke({"raw_text": text}, config={"recursion_limit": 100})
    return AttrDict(result)


def review_with_hitl(text: str) -> tuple[ReviewState, str, bool]:
    """带 human-in-the-loop 的审查:在替代方案推荐前暂停。

    返回 (state, thread_id, needs_resume)。
    needs_resume=True 表示在 recommend 前暂停了,需要调 resume_review() 继续。
    """
    graph = get_review_graph_hitl()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
    result = graph.invoke({"raw_text": text}, config=config)

    # 检查是否被 interrupt_before 暂停
    state = graph.get_state(config)
    needs_resume = len(state.next) > 0

    return AttrDict(result), thread_id, needs_resume


def resume_review(thread_id: str) -> ReviewState:
    """恢复被中断的审查流程。

    药师确认风险评估后调用,从 recommend 节点继续执行。
    用 Command(resume=True) 恢复 LangGraph interrupt_before 暂停。
    """
    graph = get_review_graph_hitl()
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(Command(resume=True), config=config)
    return AttrDict(result)


def review_prescription_stream(text: str):
    """生成器:逐步产出审查进度,最终产出完整结果。

    面试要点:用 LangGraph 的 stream mode 逐步获取每个节点的执行结果,
    前端可以实时展示当前执行到哪一步,提升用户体验。

    Yields:
        {"step": "parse", "label": "📋 解析处方", "status": "running"}
        {"step": "detect", "label": "🔍 检测药物交互", "status": "running"}
        {"step": "rules", "label": "📐 规则引擎检查", "status": "running"}
        {"step": "assess", "label": "⚠️ 评估风险等级", "status": "running"}
        {"step": "recommend", "label": "💊 推荐替代方案", "status": "running"}
        {"step": "report", "label": "📝 生成审查报告", "status": "running"}
        {"step": "complete", "label": "✅ 审查完成", "status": "done", "result": {...}}
    """
    graph = get_review_graph()

    node_labels = {
        "parse": "📋 解析处方",
        "detect": "🔍 检测药物交互",
        "rules": "📐 规则引擎检查",
        "assess": "⚠️ 评估风险等级",
        "recommend": "💊 推荐替代方案",
        "gen_report": "📝 生成审查报告",
    }

    try:
        # 自动完成模式没有 checkpointer,直接从流式输出累积最终状态
        result: dict = {"raw_text": text}
        for chunk in graph.stream({"raw_text": text}, config={"recursion_limit": 100}):
            for node_name, values in chunk.items():
                if isinstance(values, dict):
                    result.update(values)
                yield {
                    "step": node_name,
                    "label": node_labels.get(node_name, node_name),
                    "status": "running",
                }

        yield {
            "step": "complete",
            "label": "✅ 审查完成",
            "status": "done",
            "result": AttrDict(result),
        }
    except Exception as e:
        logger.exception("审查流式执行失败")
        yield {"step": "error", "label": f"❌ 错误: {e}", "status": "error"}
