# -*- coding: utf-8 -*-
"""处方解析健壮性测试（防回归）。

背景（真实踩过的坑，且是本项目最危险的一个 bug）：
    `parse_prescription` 早期有一行 `re.sub(r':\\s*null', ': ""', content)`，
    把所有 JSON null 统一替换成空串。于是 LLM 输出的 `"age": null` 变成 `"age": ""`，
    过不了 `int | None` 校验 → **整张处方解析抛异常** → 退回空 Prescription。
    下游看到"药物列表为空"，顺理成章给出 **safe**。
    也就是说：一张写着「华法林 + 阿司匹林」的处方，被系统判为「安全」。

    这是安全关键系统最坏的失败模式——把「我解析失败」当成「这张处方没风险」。
    修复分三层，本文件逐层守住：
      1. 数据层：PatientInfo 容错归一化，缺失信息不再拖垮整张处方
      2. 兜底层：解析失败/零药物时启用字面匹配兜底，而不是返回空处方
      3. 红线层：原文非空却零药物，风险等级强制 unknown 并提示人工复核
"""
import time

import pytest

from app.agents.prescription_agent import (
    DrugItem,
    PatientInfo,
    Prescription,
    _fallback_parse,
    _parse_once,
    parse_prescription,
)


# ---------- 第 1 层：字段容错 ----------

@pytest.mark.parametrize("raw,expected", [
    ("", None),
    (None, None),
    ("null", None),
    ("未知", None),
    ("不详", None),
    ("未提供", None),
    ("68岁", 68),
    ("68", 68),
    (68, 68),
    (68.0, 68),
])
def test_age_field_tolerates_missing_forms(raw, expected):
    """"年龄缺失"的任何写法都不能让校验失败。"""
    assert PatientInfo(age=raw).age == expected


def test_patientinfo_keeps_real_values():
    p = PatientInfo(age=72, gender="男", conditions=["房颤"], liver_function="impaired")
    assert (p.age, p.gender, p.liver_function) == (72, "男", "impaired")
    assert p.conditions == ["房颤"]
    assert p.renal_function == "normal"  # 未给 → 用默认值


def test_conditions_accepts_bare_string():
    """模型偶尔把 conditions 输出成字符串而不是数组。"""
    assert PatientInfo(conditions="高血压").conditions == ["高血压"]
    assert PatientInfo(conditions="").conditions == []


# ---------- 第 2 层：解析兜底 ----------

class _FakeResp:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    """返回固定内容的假 LLM，避免测试依赖网络。"""

    def __init__(self, content):
        self._content = content
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return _FakeResp(self._content)


def test_parse_once_accepts_json_null_age(monkeypatch):
    """关键回归：JSON 里的 null 不再被替换成空串，age 校验必须过。"""
    payload = ('{"drugs": [{"name": "华法林", "dosage": "5mg"}], '
               '"patient": {"age": null, "gender": "", "conditions": []}, '
               '"diagnosis": "房颤"}')
    fake = _FakeLLM(payload)
    monkeypatch.setattr("app.agents.prescription_agent.get_llm", lambda: fake)

    result = _parse_once("华法林 5mg qd")
    assert [d.name for d in result.drugs] == ["华法林"]
    assert result.patient.age is None


def test_parse_once_tolerates_fenced_and_chatty_output(monkeypatch):
    """模型前后夹带 ```json 和说明文字时仍要能解析。"""
    payload = ('好的，这是结果：\n```json\n'
               '{"drugs": ["阿司匹林"], "patient": {"age": "68岁"}}\n'
               '```\n希望有帮助')
    monkeypatch.setattr("app.agents.prescription_agent.get_llm",
                        lambda: _FakeLLM(payload))
    result = _parse_once("阿司匹林 100mg qd，患者68岁")
    assert [d.name for d in result.drugs] == ["阿司匹林"]
    assert result.patient.age == 68


def test_parse_once_drops_nameless_drugs(monkeypatch):
    payload = '{"drugs": [{"name": ""}, {"name": "布洛芬"}], "patient": {}}'
    monkeypatch.setattr("app.agents.prescription_agent.get_llm",
                        lambda: _FakeLLM(payload))
    result = _parse_once("布洛芬")
    assert [d.name for d in result.drugs] == ["布洛芬"]


def test_parse_prescription_falls_back_when_llm_keeps_failing(monkeypatch):
    """LLM 连续失败时，不能返回空处方——必须用字面兜底把药认出来。"""
    monkeypatch.setattr(time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "app.agents.prescription_agent._parse_once",
        lambda _t: (_ for _ in ()).throw(RuntimeError("LLM 不可用")),
    )
    result = parse_prescription("阿司匹林 100mg 每日一次;华法林 5mg 每日一次")
    names = [d.name for d in result.drugs]
    assert "阿司匹林" in names and "华法林" in names, f"兜底失败: {names}"


def test_parse_prescription_retries_then_falls_back_on_empty(monkeypatch):
    """解析成功但一个药都没认出来，同样视为失败并转兜底。"""
    monkeypatch.setattr(time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "app.agents.prescription_agent._parse_once",
        lambda _t: Prescription(diagnosis="", drugs=[], patient=PatientInfo()),
    )
    result = parse_prescription("患者服用 二甲双胍 500mg bid")
    assert [d.name for d in result.drugs], "零药物结果必须触发兜底，不能原样返回"


def test_fallback_parse_does_not_duplicate_nested_names():
    """'阿司匹林肠溶片' 之类不应被 '阿司匹林' 重复命中。"""
    result = _fallback_parse("阿司匹林 100mg qd")
    names = [d.name for d in result.drugs]
    assert len(names) == len(set(names)), f"出现重复药名: {names}"


def test_empty_input_returns_empty_prescription():
    """"真的什么都没输入"不应触发兜底（也没有可兜底的内容）。"""
    result = parse_prescription("   ")
    assert result.drugs == []


# ---------- 第 3 层：工作流红线 ----------

def test_assess_marks_unknown_when_no_drug_recognized(monkeypatch):
    """原文非空却零药物 → 风险未知 + 人工复核提示，绝不能是 safe。"""
    import app.workflow as wf
    from app.agents.risk_agent import RiskAssessment

    monkeypatch.setattr(
        wf, "assess_risk",
        lambda **_kw: RiskAssessment(overall_risk="safe", risks=[], summary=""),
    )
    state = {
        "raw_text": "患者男68岁，服用华法林 5mg qd 与 阿司匹林 100mg qd",
        "drug_names": [],
        "drugs_info": [],
        "patient": {},
        "interactions": [],
        "contraindications": [],
        "rule_risks": [],
    }
    out = wf.node_assess(state)
    ra = out["risk_assessment"]
    assert ra.overall_risk == "unknown", "解析失败却给出 safe，是最危险的假阴性"
    assert len(ra.risks) == 1
    assert "人工复核" in ra.risks[0].description
    assert ra.summary


def test_assess_leaves_normal_result_untouched(monkeypatch):
    """正常识别出药物时，不得误触发兜底。"""
    import app.workflow as wf
    from app.agents.risk_agent import RiskAssessment

    monkeypatch.setattr(
        wf, "assess_risk",
        lambda **_kw: RiskAssessment(overall_risk="high", risks=[], summary="出血风险"),
    )
    state = {
        "raw_text": "华法林 5mg qd; 阿司匹林 100mg qd",
        "drug_names": ["华法林", "阿司匹林"],
        "drugs_info": [{"name": "华法林"}, {"name": "阿司匹林"}],
        "patient": {},
        "interactions": [],
        "contraindications": [],
        "rule_risks": [],
    }
    ra = wf.node_assess(state)["risk_assessment"]
    assert ra.overall_risk == "high"
    assert ra.risks == []


# ---------- 缓存红线 ----------

def test_parse_failure_result_is_not_cached():
    """解析失败（零药物 / unknown）的结果不得写入缓存。"""
    from app.routers.review import _is_review_cacheable

    class _RA:
        overall_risk = "safe"

    class _RX:
        drugs = []

    class _State:
        prescription = _RX()
        risk_assessment = _RA()

    assert _is_review_cacheable(_State()) is False, "零药物结果被判定为可缓存"

    class _RX2:
        drugs = [DrugItem(name="华法林")]

    class _State2:
        prescription = _RX2()
        risk_assessment = _RA()

    assert _is_review_cacheable(_State2()) is True

    # 响应 dict 形式同样适用
    assert _is_review_cacheable({"prescription": {"drugs": []}, "risk_level": "safe"}) is False
    assert _is_review_cacheable(
        {"prescription": {"drugs": [{"name": "华法林"}]}, "risk_level": "unknown"}
    ) is False
    assert _is_review_cacheable(
        {"prescription": {"drugs": [{"name": "华法林"}]}, "risk_level": "high"}
    ) is True
