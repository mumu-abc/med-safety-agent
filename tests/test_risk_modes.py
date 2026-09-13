"""风险评估路径测试（RISK_MODE=rules，不依赖 LLM）。"""
from app.agents.risk_agent import assess_risk


def test_rules_mode_uses_deterministic_floor(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "risk_mode", "rules")

    result = assess_risk(
        interactions=[{
            "drug_a": "华法林", "drug_b": "布洛芬",
            "severity": "critical", "mechanism": "出血风险",
        }],
        contraindications=[],
        rule_risks=[],
        patient={"age": 70, "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
        drugs=[{"id": "warfarin", "name": "华法林"}, {"id": "ibuprofen", "name": "布洛芬"}],
    )
    assert result.overall_risk == "critical"
    assert any(r.source == "graph" for r in result.risks)


def test_rules_mode_safe_when_nothing_found(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "risk_mode", "rules")

    result = assess_risk(
        interactions=[], contraindications=[], rule_risks=[],
        patient={"age": 40, "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
        drugs=[{"id": "amlodipine", "name": "氨氯地平"}],
    )
    assert result.overall_risk == "safe"
