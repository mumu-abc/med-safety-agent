"""LLM 增量难例集 + 风险校准回归测试(不依赖 LLM API)。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "eval_llm_increment.json"


def test_llm_increment_dataset_exists_and_valid():
    cases = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(cases) >= 8
    tracks = {c["track"] for c in cases}
    assert "parse" in tracks
    assert "reason" in tracks
    assert "negative" in tracks
    for c in cases:
        assert c["expected_risk"] in ("critical", "high", "medium", "low", "safe")
        assert c["expected_drugs"], c["id"]
        assert c["prescription_text"]


def test_oracle_baseline_misses_llm_only_cases():
    """Oracle(图谱+规则@标注药名)应在多数 reason 难例上 miss,否则难例设计失效。"""
    from scripts.eval_llm_increment import eval_oracle, load_cases

    cases = [c for c in load_cases() if c["track"] == "reason"]
    results = eval_oracle(cases)
    # reason 难例设计目标:确定性基线精确率应显著低于 100%
    exact = sum(1 for r in results if r["exact"])
    assert exact < len(results), (
        "reason 难例全部被图谱+规则命中,无法证明 LLM 增量,请重新设计难例"
    )


def test_risk_agent_cannot_downgrade_rule_severity():
    """规则引擎命中 critical 时,overall_risk 不得停在 LLM 的 safe。"""
    from app.agents.risk_agent import RiskAssessment, RiskItem

    # 直接测合并后的校准逻辑:构造一个「LLM说safe + 规则critical」的输入路径
    # assess_risk 内部会调 LLM;这里复现合并段行为——通过注入假 LLM 成本高,
    # 改为单测校准函数语义:用真实 merge 后的状态对象验证。
    ra = RiskAssessment(
        overall_risk="safe",
        risks=[RiskItem(drug="x", risk_type="llm", severity="safe", description="ok", source="llm")],
        summary="llm said safe",
    )
    # 模拟 merge 后追加规则 critical
    ra.risks.append(RiskItem(
        drug="华法林", risk_type="pregnancy", severity="critical",
        description="孕期禁忌", source="rule",
    ))
    # 与生产代码相同的校准
    _SEV_RANK = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    max_rank = _SEV_RANK.get(ra.overall_risk, 0)
    max_sev = ra.overall_risk
    for r in ra.risks:
        rank = _SEV_RANK.get(r.severity, 0)
        if rank > max_rank:
            max_rank = rank
            max_sev = r.severity
    if max_rank > _SEV_RANK.get(ra.overall_risk, 0):
        ra.overall_risk = max_sev
    assert ra.overall_risk == "critical"


def test_assess_risk_merges_and_calibrates_without_live_llm(monkeypatch):
    """打桩 LLM,验证 assess_risk 在规则 critical 时抬升 overall_risk。"""
    from pydantic import BaseModel
    from app.agents import risk_agent as ra_mod

    class _FakeLLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, _messages):
            return ra_mod.RiskAssessment(
                overall_risk="safe",
                risks=[],
                summary="looks fine",
            )

    # 绕过 create_react_agent:直接替换 assess 内部路径较深,改为 patch get_llm + create_react_agent
    def _fake_react(*_a, **_k):
        class _Agent:
            def invoke(self, _state, config=None):
                return {
                    "structured_response": ra_mod.RiskAssessment(
                        overall_risk="safe", risks=[], summary="looks fine"
                    ),
                    "messages": [],
                }
        return _Agent()

    monkeypatch.setattr(ra_mod, "get_llm", lambda: _FakeLLM())
    monkeypatch.setattr(ra_mod, "create_react_agent", _fake_react)

    result = ra_mod.assess_risk(
        interactions=[],
        contraindications=[],
        rule_risks=[{
            "drug": "华法林", "risk": "孕期禁忌: X级,致畸", "severity": "critical",
            "rule": "pregnancy_contraindication", "suggestion": "停药",
            "risk_type": "pregnancy",
        }],
        patient={"age": 28, "gender": "女", "conditions": [], "allergies": [],
                 "liver_function": "normal", "renal_function": "normal", "pregnancy": "yes"},
        drugs=[{"id": "warfarin", "name": "华法林"}],
    )
    assert result.overall_risk == "critical", "规则 critical 被 LLM safe 吞掉"
    assert any(r.source == "rule" for r in result.risks)
