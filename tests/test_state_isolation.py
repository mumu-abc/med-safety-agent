"""回归测试:锁住"跨请求状态残留"与"缓存键缺维度"两个缺陷。

背景:
1. 自动完成模式曾给所有审查共用一个固定 thread_id + MemorySaver,导致条件边
   跳过 `recommend` 节点时,`alternatives` 保留上一次审查的值 —— 用户 B 会拿到
   用户 A 的换药建议。
2. 审查缓存只按处方文本哈希,忽略 patient_id 与审查模式,导致不同患者/不同接口
   互相污染缓存,且缓存永不过期。
"""
import pytest

import app.workflow as wf
from app.models import Prescription, Drug, PatientInfo
from app.agents.risk_agent import RiskAssessment, RiskItem
from app.agents.alternative_agent import (
    AlternativeReport, AlternativeSuggestion, AlternativeDrug,
)


# ---- 固定 thread_id 导致的状态残留 ----

@pytest.fixture
def stubbed_graph(monkeypatch):
    """Stub 掉所有 LLM 依赖,只保留 LangGraph 状态机本身。"""
    state = {"risk": "high"}

    def fake_parse(text):
        return Prescription(
            diagnosis="test",
            drugs=[Drug(name="DrugA", dosage="5mg", frequency="qd")],
            patient=PatientInfo(),
        )

    def fake_detect(drug_names, conditions=None):
        return {"interactions": [], "contraindications": []}

    def fake_rules(drugs_info, patient):
        return []

    def fake_assess(**kwargs):
        return RiskAssessment(
            overall_risk=state["risk"],
            risks=[RiskItem(drug="DrugA", risk_type="interaction", severity="high",
                            description="d", source="s", suggestion="x")],
            summary=f"summary-{state['risk']}",
        )

    def fake_recommend(**kwargs):
        return AlternativeReport(
            suggestions=[AlternativeSuggestion(
                original_drug="DrugA",
                alternatives=[AlternativeDrug(name="AltX", category="c", reason="r")],
                reason="rr")],
            summary="来自上一次审查的替代方案",
        )

    monkeypatch.setattr(wf, "parse_prescription", fake_parse)
    monkeypatch.setattr(wf, "detect_interactions", fake_detect)
    monkeypatch.setattr(wf, "run_all_rules", fake_rules)
    monkeypatch.setattr(wf, "assess_risk", fake_assess)
    monkeypatch.setattr(wf, "recommend_alternatives", fake_recommend)
    monkeypatch.setattr(wf, "generate_report", lambda s: "report")
    return state


def test_no_state_leak_between_reviews(stubbed_graph):
    """低风险的第二次审查,绝不能继承第一次的 alternatives。"""
    stubbed_graph["risk"] = "high"
    r1 = wf.review_prescription("处方A:华法林")
    assert r1.get("alternatives") is not None, "高风险应触发替代方案推荐"

    stubbed_graph["risk"] = "low"
    r2 = wf.review_prescription("处方B:维生素C")
    assert r2.get("alternatives") is None, (
        "低风险处方继承了上一次审查的替代方案 —— 跨请求状态残留"
    )


def test_stream_result_contains_all_fields(stubbed_graph):
    """流式审查也必须在结束时产出完整状态。"""
    stubbed_graph["risk"] = "high"
    steps = list(wf.review_prescription_stream("处方A:华法林"))
    done = [s for s in steps if s["step"] == "complete"]
    assert len(done) == 1
    result = done[0]["result"]
    assert result["risk_assessment"].overall_risk == "high"
    assert result.get("alternatives") is not None


# ---- 缓存键维度与过期 ----

def test_cache_key_includes_patient_and_mode(tmp_path, monkeypatch):
    """同一处方在不同患者/不同模式下必须是不同的缓存条目。"""
    import app.database as dbmod
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "cache_test.db")
    db = dbmod.Database()

    db.save_review_cache("华法林 5mg", {"v": 1}, patient_id="", mode="raw")
    db.save_review_cache("华法林 5mg", {"v": 2}, patient_id="p001", mode="raw")
    db.save_review_cache("华法林 5mg", {"v": 3}, patient_id="", mode="multi")

    assert db.get_cached_review("华法林 5mg", patient_id="", mode="raw")["v"] == 1
    assert db.get_cached_review("华法林 5mg", patient_id="p001", mode="raw")["v"] == 2
    assert db.get_cached_review("华法林 5mg", patient_id="", mode="multi")["v"] == 3
    # 未指定模式(旧调用方)不应命中带模式的条目
    assert db.get_cached_review("华法林 5mg") is None


def test_cache_respects_ttl(tmp_path, monkeypatch):
    """超过 TTL 的缓存必须视为未命中。"""
    import app.database as dbmod
    from datetime import datetime, timedelta
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "ttl_test.db")
    db = dbmod.Database()

    db.save_review_cache("阿司匹林 100mg", {"v": 1}, mode="raw")
    assert db.get_cached_review("阿司匹林 100mg", mode="raw") is not None

    old = (datetime.now() - timedelta(days=30)).isoformat()
    db._get_conn().execute("UPDATE review_cache SET created_at = ?", (old,))
    db._get_conn().commit()

    assert db.get_cached_review("阿司匹林 100mg", mode="raw") is None, (
        "过期缓存仍被返回,审查结论会长期停留在旧结果上"
    )
