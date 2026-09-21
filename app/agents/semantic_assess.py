"""轻量语义风险评估:单次 structured output,不走 ReAct 工具循环。

用途:
  1. LLM 增量评测 Track C —— 稳定、可计时、不依赖工具调用是否可用
  2. ReAct Agent 失败/超时后的安全兜底 —— 保证「规则结果 + LLM 补充」仍能出报告

设计要点:Agent 不是只有一种调用形态。生产默认 ReAct(可查图谱工具),
离线评测与故障降级用单次结构化推理,便于做受控对比实验。
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.llm import get_llm

logger = logging.getLogger(__name__)


class LLMRiskItem(BaseModel):
    drug: str = Field(default="", description="涉及药物")
    risk_type: str = Field(default="llm", description="风险类型")
    severity: str = Field(default="medium", description="critical/high/medium/low/safe")
    description: str = Field(default="", description="风险描述")
    suggestion: str = Field(default="", description="处理建议")


class LLMRiskAssessment(BaseModel):
    overall_risk: str = Field(default="unknown", description="critical/high/medium/low/safe")
    risks: list[LLMRiskItem] = Field(default_factory=list)
    summary: str = Field(default="")


SYSTEM = """你是资深临床药师。在给定患者与处方下,评估用药安全。
规则引擎已给出硬性风险(必须保留,不得降级)。你的职责是补充规则/图谱覆盖不到的问题:
- 剂量是否明显超说明书(如对乙酰氨基酚日剂量≥4g → high)
- 病史/化验值与药物的语义冲突(如 eGFR<30+二甲双胍)
- 商品名/成分重复用药
- 图谱外但临床明确的药理风险
- 文本中隐含的肝肾功能等关键信息

严重程度校准(严格执行,禁止随意升到 critical):
- critical: 很可能导致死亡或不可逆严重损害,需立即停药/抢救级干预
  例: 孕期禁用致畸药、抗凝+NSAID、SSRI+MAOI、严重肾功能不全禁用药、多药呼吸抑制
- high: 需要临床干预或调整方案,否则风险显著升高
  例: 达说明书日剂量上限、重复用药、重要病史禁忌、双联抗血小板
- medium: 需监测,可在观察下继续
- safe: 当前条件下无需干预

没有需要干预的问题时输出 safe。不要因为「所有药都有副作用」就报警。
也不要为了保守把 high 拔高成 critical——只有符合上面 critical 定义才允许。
"""


def build_context_text(
    prescription_text: str,
    drugs: list[dict] | None = None,
    patient: dict | None = None,
    rule_risks: list[dict] | None = None,
    interactions: list[dict] | None = None,
) -> str:
    parts = ["## 原始处方文本", prescription_text or ""]
    if patient:
        parts.append("\n## 结构化患者信息")
        for k in ("age", "gender", "conditions", "allergies", "liver_function", "renal_function", "pregnancy"):
            if k in patient:
                parts.append(f"- {k}: {patient[k]}")
    if drugs:
        parts.append("\n## 已识别药物")
        for d in drugs:
            parts.append(f"- {d.get('name','')} {d.get('dosage','')} {d.get('frequency','')}")
    if interactions:
        parts.append("\n## 图谱交互(必须保留)")
        for it in interactions:
            parts.append(f"- {it.get('drug_a')}+{it.get('drug_b')}: {it.get('severity')} — {it.get('mechanism','')}")
    if rule_risks:
        parts.append("\n## 规则引擎命中(必须保留,不得降级)")
        for rr in rule_risks:
            parts.append(f"- [{rr.get('severity')}] {rr.get('drug')}: {rr.get('risk')}")
    return "\n".join(parts)


def assess_risk_llm_once(context: str) -> LLMRiskAssessment:
    """单次 structured-output 风险评估。"""
    llm = get_llm()
    structured = llm.with_structured_output(LLMRiskAssessment)
    result = structured.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"请评估以下用药安全:\n\n{context}"),
    ])
    if not isinstance(result, LLMRiskAssessment):
        # 兼容 dict 返回
        result = LLMRiskAssessment.model_validate(result)
    raw = (result.overall_risk or "unknown").strip().lower()
    mapping = {
        "critical": "critical", "high": "high", "medium": "medium",
        "moderate": "medium", "low": "low", "safe": "safe",
        "危急": "critical", "高": "high", "中": "medium", "低": "low", "安全": "safe",
    }
    result.overall_risk = mapping.get(raw, "unknown")
    return result


def merge_rule_floor(overall_risk: str, llm_risks: list, rule_risks: list[dict] | None) -> tuple[str, list]:
    """合并规则风险并保证 overall_risk 不低于规则最高 severity。"""
    from app.agents.risk_agent import RiskItem

    merged: list[RiskItem] = []
    for r in llm_risks or []:
        if isinstance(r, RiskItem):
            merged.append(r)
        else:
            merged.append(RiskItem(
                drug=getattr(r, "drug", "") or (r.get("drug", "") if isinstance(r, dict) else ""),
                risk_type="llm",
                severity=getattr(r, "severity", "medium") or "medium",
                description=getattr(r, "description", "") or "",
                source="llm",
                suggestion=getattr(r, "suggestion", "") or "",
            ))
    existing = {(x.risk_type, x.drug) for x in merged}
    for rr in rule_risks or []:
        key = (rr.get("risk_type", "rule"), rr.get("drug", ""))
        if key in existing:
            continue
        merged.append(RiskItem(
            drug=rr.get("drug", ""), risk_type=rr.get("risk_type", "rule"),
            severity=rr.get("severity", "high"), description=rr.get("risk", ""),
            source="rule", suggestion=rr.get("suggestion", ""),
        ))
    rank = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    best = overall_risk
    best_r = rank.get(overall_risk, 0)
    for item in merged:
        r = rank.get(item.severity, 0)
        if r > best_r:
            best_r, best = r, item.severity
    return best, merged
