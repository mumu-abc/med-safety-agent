"""端到端测试:mock LLM,测完整流程。"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.drug_data import build_graph_from_data


def _mock_parse_prescription(text: str):
    from app.agents.prescription_agent import Prescription, DrugItem, PatientInfo
    return Prescription(
        drugs=[
            DrugItem(name="华法林", dosage="2.5mg", frequency="qd"),
            DrugItem(name="阿司匹林", dosage="100mg", frequency="qd"),
            DrugItem(name="布洛芬", dosage="400mg", frequency="prn"),
        ],
        patient=PatientInfo(age=65, gender="男", conditions=["高血压", "冠心病"]),
        diagnosis="冠心病",
    )


def _mock_detect_interactions(drug_names, patient_conditions=None):
    """Mock 交互检测(返回真实图谱数据)。"""
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    ids = [get_drug_by_name(n)["id"] for n in drug_names if get_drug_by_name(n)]
    interactions = find_interactions(ids) if len(ids) >= 2 else []
    contras = []
    if patient_conditions:
        for name in drug_names:
            d = get_drug_by_name(name)
            if d:
                contras.extend(find_contraindications(d["id"], patient_conditions))
    return {"tool_calls": [], "interactions": interactions, "contraindications": contras}


def _mock_assess_risk(interactions, contraindications, rule_risks, patient, drugs):
    from app.agents.risk_agent import RiskAssessment, RiskItem
    risks = []
    for it in interactions:
        risks.append(RiskItem(
            drug=f"{it['drug_a']}+{it['drug_b']}", risk_type="interaction",
            severity=it["severity"], description=it["mechanism"], source="llm",
        ))
    for rr in rule_risks:
        risks.append(RiskItem(
            drug=rr["drug"], risk_type="rule", severity=rr["severity"],
            description=rr["risk"], source="rule", suggestion=rr.get("suggestion", ""),
        ))
    overall = "critical" if any(r.severity == "critical" for r in risks) else "high"
    return RiskAssessment(overall_risk=overall, risks=risks, summary="多药联用出血风险极高")


def _mock_recommend_alternatives(high_risk_drugs, current_drug_names, patient, risk_assessment=None):
    from app.agents.alternative_agent import AlternativeReport, AlternativeSuggestion
    return AlternativeReport(
        suggestions=[AlternativeSuggestion(
            original_drug="布洛芬",
            alternatives=[{"name": "对乙酰氨基酚", "category": "解热镇痛药"}],
            reason="对乙酰氨基酚不增加消化道出血风险",
        )],
        summary="建议停布洛芬,换对乙酰氨基酚",
    )


def test_e2e_high_risk():
    """测试高危处方的完整审查流程。"""
    build_graph_from_data()

    import app.workflow
    with patch.object(app.workflow, "parse_prescription", _mock_parse_prescription), \
         patch.object(app.workflow, "detect_interactions", _mock_detect_interactions), \
         patch.object(app.workflow, "assess_risk", _mock_assess_risk), \
         patch.object(app.workflow, "recommend_alternatives", _mock_recommend_alternatives):

        result = app.workflow.review_prescription("患者王某,男,65岁,冠心病,处方:华法林+阿司匹林+布洛芬")

        assert result.prescription is not None
        assert len(result.drug_names) == 3
        assert len(result.interactions) >= 2, f"应检测到至少2条相互作用,实际{len(result.interactions)}"
        severities = {i["severity"] for i in result.interactions}
        assert "critical" in severities
        assert len(result.rule_risks) >= 1
        assert result.risk_assessment is not None
        assert result.risk_assessment.overall_risk == "critical"
        assert result.alternatives is not None
        assert "审查报告" in result.report
        assert "华法林" in result.report

        print(f"✅ E2E测试通过: {len(result.interactions)}条交互, {len(result.rule_risks)}条规则风险")
        print(f"   风险等级: {result.risk_assessment.overall_risk}")


def test_e2e_safe_prescription():
    """测试安全处方。"""
    build_graph_from_data()

    def _mock_parse_safe(text):
        from app.agents.prescription_agent import Prescription, DrugItem, PatientInfo
        return Prescription(
            drugs=[
                DrugItem(name="氨氯地平", dosage="5mg", frequency="qd"),
                DrugItem(name="对乙酰氨基酚", dosage="500mg", frequency="prn"),
            ],
            patient=PatientInfo(age=45, gender="女", conditions=["高血压"]),
            diagnosis="高血压",
        )

    def _mock_detect_safe(drug_names, patient_conditions=None):
        return {"tool_calls": [], "interactions": [], "contraindications": []}

    def _mock_assess_safe(interactions, contraindications, rule_risks, patient, drugs):
        from app.agents.risk_agent import RiskAssessment
        return RiskAssessment(overall_risk="safe", risks=[], summary="无明显用药风险")

    import app.workflow
    with patch.object(app.workflow, "parse_prescription", _mock_parse_safe), \
         patch.object(app.workflow, "detect_interactions", _mock_detect_safe), \
         patch.object(app.workflow, "assess_risk", _mock_assess_safe):

        result = app.workflow.review_prescription("患者赵某,女,45岁,高血压,处方:氨氯地平+对乙酰氨基酚")

        assert result.risk_assessment.overall_risk == "safe"
        assert len(result.interactions) == 0
        print(f"✅ 安全处方测试通过: 风险等级 safe, 无相互作用")


if __name__ == "__main__":
    test_e2e_high_risk()
    test_e2e_safe_prescription()
    print("\n🎉 所有E2E测试通过!")
