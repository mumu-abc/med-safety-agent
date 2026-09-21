"""确定性地板的「可解释性」契约测试。

背景:
    assess_risk 里有一条"规则/图谱地板" —— 最终 overall_risk 不得低于图谱/规则
    命中风险的最高 severity，LLM 想把 critical 降成 safe 是不行的。
    但改造之前，这件事**只有一条 logger.warning**：不进接口响应、不进报告、不进界面。
    后果：药师看到「极高危」时，无法分辨这是 LLM 自己判的，还是规则从低危强制抬上来的。
    医疗 AI 里这属于 explainability / auditability 缺口。

改造后锁住下面这些契约:
    · 抬升时置 floor_applied=True 并记下 LLM 的原判(llm_original_risk）
    · LLM 没给出可解析等级时同样要置位（结论实际由规则决定）
    · 两个字段是**系统字段**，必须排除出 LLM 的 structured-output JSON Schema
      （否则 ReAct 的 response_format 会要求模型输出它判断不了的东西）
    · 接口响应体要透出这两个字段（前端据此显示提示）
    · 推理链不能再说"LLM 判定为 X"（地板生效时这句话是假的）
    · 结构过期的缓存（老缓存没这个字段）必须作废重算，否则提示被静默吞掉
"""
from __future__ import annotations

_PATIENT = {
    "age": 70, "gender": "男", "conditions": [], "allergies": [],
    "liver_function": "normal", "renal_function": "normal", "pregnancy": "no",
}
_DRUGS = [{"id": "warfarin", "name": "华法林"}, {"id": "ibuprofen", "name": "布洛芬"}]

# 规则引擎命中 critical —— 这就是"地板"的来源
_CRITICAL_RULE = [{
    "drug": "华法林", "risk": "孕期禁忌", "severity": "critical",
    "rule": "pregnancy_contraindication", "suggestion": "停药", "risk_type": "pregnancy",
}]

_HIGH_INTERACTION = [{
    "drug_a": "华法林", "drug_b": "布洛芬", "severity": "high", "mechanism": "出血风险",
}]


def _stub_semantic_llm(monkeypatch, level: str):
    """把 semantic 路径的 LLM 换成固定输出的假实现，返回 risk_agent 模块。

    注意 semantic 路径实际调用的是 app.agents.semantic_assess.get_llm
    （不是 risk_agent.get_llm），必须打到真正那一个上，否则会静默走"LLM 不可用"分支，
    测试就会"因为错误的原因通过"。
    假实现返回 dict —— semantic_assess 里用 LLMRiskAssessment.model_validate(result) 兼容 dict。
    """
    from app.agents import risk_agent as ra_mod
    from app.agents import semantic_assess
    from app.config import settings

    monkeypatch.setattr(settings, "risk_mode", "semantic")

    class _FakeLLM:
        def with_structured_output(self, _schema):
            return self

        def invoke(self, _messages, *_a, **_k):
            return {"overall_risk": level, "risks": [], "summary": "stub-llm"}

    monkeypatch.setattr(semantic_assess, "get_llm", lambda: _FakeLLM())
    return ra_mod


def test_floor_raise_marks_floor_applied_with_llm_original(monkeypatch):
    """LLM 判 safe、规则是 critical → 抬升，并记下 LLM 的原判。"""
    ra_mod = _stub_semantic_llm(monkeypatch, "safe")

    result = ra_mod.assess_risk(
        interactions=[], contraindications=[], rule_risks=_CRITICAL_RULE,
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.overall_risk == "critical", "规则 critical 被 LLM safe 吞掉"
    assert result.floor_applied is True, "地板生效却没有标记，药师无从判断"
    assert result.llm_original_risk == "safe", "没有如实记下 LLM 的原判"


def test_floor_not_applied_when_llm_already_at_floor(monkeypatch):
    """LLM 自己也判 critical → 不算被抬升；但 LLM 的原判仍要如实记录。"""
    ra_mod = _stub_semantic_llm(monkeypatch, "critical")

    result = ra_mod.assess_risk(
        interactions=[], contraindications=[], rule_risks=_CRITICAL_RULE,
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.overall_risk == "critical"
    assert result.floor_applied is False, "LLM 自己判到的等级不应被标成'规则抬升'"
    assert result.llm_original_risk == "critical", "LLM 参与了就该记录它的原判"


def test_llm_above_floor_is_kept_and_not_flagged(monkeypatch):
    """LLM 判得比规则更高 → 保留 LLM 的结论，不算地板生效（地板只防降级）。"""
    ra_mod = _stub_semantic_llm(monkeypatch, "critical")

    result = ra_mod.assess_risk(
        interactions=[], contraindications=[], rule_risks=[],
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.overall_risk == "critical"
    assert result.floor_applied is False
    assert result.llm_original_risk == "critical"


def test_empty_llm_original_risk_means_no_llm_participation(monkeypatch):
    """空字符串的语义必须唯一：只有"LLM 压根没参与"才会是空。"""
    from app.agents import semantic_assess
    from app.agents.risk_agent import assess_risk
    from app.config import settings

    monkeypatch.setattr(settings, "risk_mode", "semantic")

    def _boom():
        raise RuntimeError("llm unavailable")

    monkeypatch.setattr(semantic_assess, "get_llm", _boom)

    result = assess_risk(
        interactions=[], contraindications=[], rule_risks=[],
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.llm_original_risk == "", "LLM 未参与时才允许为空"
    assert result.floor_applied is False
    assert "LLM" in result.summary


def test_unparseable_llm_level_is_flagged_as_unknown(monkeypatch):
    """LLM 没给出可解析等级 → 结论实际由规则/图谱决定，同样要标出来。"""
    ra_mod = _stub_semantic_llm(monkeypatch, "看不懂的等级")

    result = ra_mod.assess_risk(
        interactions=_HIGH_INTERACTION, contraindications=[], rule_risks=[],
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.overall_risk == "high"
    assert result.floor_applied is True
    assert result.llm_original_risk == "unknown"


def test_rules_mode_has_no_llm_judgement(monkeypatch):
    """纯 rules 模式压根没有 LLM 判断 → 不算"抬升"，由 summary 负责说明。"""
    from app.agents.risk_agent import assess_risk
    from app.config import settings

    monkeypatch.setattr(settings, "risk_mode", "rules")

    result = assess_risk(
        interactions=_HIGH_INTERACTION, contraindications=[], rule_risks=[],
        patient=_PATIENT, drugs=_DRUGS,
    )

    assert result.overall_risk == "high"
    assert result.floor_applied is False
    assert result.llm_original_risk == ""
    assert "LLM" in result.summary
    assert any(r.source == "graph" for r in result.risks)


def test_floor_fields_excluded_from_llm_json_schema():
    """系统字段必须排除出 LLM 的输出契约，否则模型会被要求填它判断不了的东西。"""
    from app.agents.risk_agent import RiskAssessment

    props = set(RiskAssessment.model_json_schema()["properties"])
    assert props == {"overall_risk", "risks", "summary"}, f"意外的 schema: {props}"
    assert "floor_applied" not in props
    assert "llm_original_risk" not in props

    # 但序列化时必须带上（否则接口/缓存/数据库拿不到）
    dumped = RiskAssessment(
        overall_risk="high", floor_applied=True, llm_original_risk="low",
    ).model_dump()
    assert dumped["floor_applied"] is True
    assert dumped["llm_original_risk"] == "low"


def test_raw_response_exposes_floor_fields():
    """接口响应体必须透出这两个字段（前端据此显示"本条由规则抬升"提示）。"""
    from app.agents.risk_agent import RiskAssessment
    from app.routers.review import _build_raw_response

    raw = _build_raw_response({
        "risk_assessment": RiskAssessment(
            overall_risk="critical", risks=[], summary="rule forced",
            floor_applied=True, llm_original_risk="low",
        )
    })

    assert raw["risk_assessment"]["floor_applied"] is True
    assert raw["risk_assessment"]["llm_original_risk"] == "low"


def test_reasoning_chain_tells_truth_when_floor_applied():
    """地板生效时，推理链不能再说"LLM 判定为 X"。"""
    from app.agents.risk_agent import RiskAssessment
    from app.routers.review import _build_raw_response

    raw = _build_raw_response({
        "risk_assessment": RiskAssessment(
            overall_risk="critical", risks=[], summary="",
            floor_applied=True, llm_original_risk="low",
        )
    })
    step4 = next(s for s in raw["reasoning_chain"] if s["node"] == "assess")

    assert "LLM 原判为 low" in step4["detail"]
    assert "并非 LLM 判断" in step4["detail"]


def test_cache_guard_rejects_payload_without_floor_field():
    """老缓存的 risk_assessment 没有 floor_applied → 必须判过期，否则提示被静默吞掉。"""
    from app.routers.review import _is_cache_schema_current

    stale = {
        "reasoning_chain": [{"step": "①", "detail": "x", "node": "parse"}],
        "risk_assessment": {"overall_risk": "critical", "risks": [], "summary": ""},
    }
    assert _is_cache_schema_current(stale) is False

    fresh = {
        "reasoning_chain": [{"step": "①", "detail": "x", "node": "parse"}],
        "risk_assessment": {
            "overall_risk": "critical", "risks": [], "summary": "",
            "floor_applied": False, "llm_original_risk": "",
        },
    }
    assert _is_cache_schema_current(fresh) is True
