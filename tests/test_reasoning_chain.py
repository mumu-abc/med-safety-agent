# -*- coding: utf-8 -*-
"""推理链回归测试。

背景（真实的线上问题）：
    前端「🧠 推理链」tab 从上线起就是**空的** —— 它读 `data.reasoning_chain`,
    但后端 `_build_raw_response()` 从来没返回过这个字段(grep 全仓 0 命中)。
    更糟的是前端 `fillReasoning()` 在空数组时直接 `return`,连占位文案都没有,
    用户点进去看到的就是一片白。

修复:
    1. 后端从已有 state 派生 `reasoning_chain`(不额外调 LLM,成本 0)
    2. 六步与 LangGraph 节点一一对应,便于对着 trace 看
    3. 前端空数据时给占位文案,不再白屏
"""
from app.models import (
    AlternativeDrug,
    AlternativeReport,
    AlternativeSuggestion,
    Drug,
    InteractionItem,
    PatientInfo,
    Prescription,
    RiskAssessment,
)
from app.routers.review import _build_raw_response, _build_reasoning_chain


def _fake_result(**overrides):
    """构造一份「跑完的」审查结果,字段与 ReviewState 对齐。"""
    result = {
        "raw_text": "华法林 5mg qd;阿司匹林 100mg qd;布洛芬 400mg tid",
        "prescription": Prescription(
            diagnosis="房颤合并冠心病",
            drugs=[
                Drug(name="华法林", dosage="5mg", frequency="qd"),
                Drug(name="阿司匹林", dosage="100mg", frequency="qd"),
                Drug(name="布洛芬", dosage="400mg", frequency="tid"),
            ],
            patient=PatientInfo(age=68, gender="男", conditions=["冠心病", "房颤"]),
        ),
        "drug_names": ["华法林", "阿司匹林", "布洛芬"],
        "drugs_info": [],
        "patient": {"age": 68, "gender": "男", "conditions": ["冠心病", "房颤"]},
        "interactions": [
            InteractionItem(
                drug_a="华法林", drug_b="阿司匹林", severity="high",
                mechanism="抗凝+抗血小板双联,消化道出血风险显著增加",
            ).model_dump(),
            InteractionItem(drug_a="华法林", drug_b="布洛芬", severity="critical",
                            mechanism="NSAIDs增强抗凝,出血风险极高").model_dump(),
        ],
        "contraindications": [
            {"drug": "布洛芬", "condition": "冠心病", "severity": "critical",
             "suggestion": "冠心病患者避免使用"},
        ],
        "rule_risks": [
            {"drug": "布洛芬", "risk": "老年心血管患者慎用", "severity": "high",
             "suggestion": "改用对乙酰氨基酚"},
            {"drug": "华法林", "risk": "需监测 INR", "severity": "medium",
             "suggestion": "定期查凝血"},
        ],
        "risk_assessment": RiskAssessment(
            overall_risk="critical",
            summary="三联用药出血风险极高,建议停用布洛芬。",
        ),
        "alternatives": AlternativeReport(
            suggestions=[
                AlternativeSuggestion(
                    original_drug="布洛芬",
                    alternatives=[AlternativeDrug(name="对乙酰氨基酚", category="解热镇痛")],
                    reason="不抑制血小板,出血风险低",
                )
            ],
            summary="建议以对乙酰氨基酚替代布洛芬。",
        ),
        "report": "【用药安全审查报告】" + "详细内容。" * 30,
    }
    result.update(overrides)
    return result


# ---------- 核心:推理链不再是空的 ----------

def test_chain_is_not_empty():
    """回归:这个字段曾经完全不存在,导致前端 tab 白屏。"""
    chain = _build_reasoning_chain(_fake_result())
    assert chain, "推理链为空 —— 前端「推理链」tab 又会白屏"


def test_chain_covers_all_six_nodes():
    """六步必须与流水线节点一一对应,便于对着 LangSmith trace 排查。"""
    chain = _build_reasoning_chain(_fake_result())
    nodes = [s["node"] for s in chain]
    assert nodes == ["parse", "detect", "rules", "assess", "recommend", "gen_report"]


def test_every_step_has_non_empty_detail():
    """每一步都要有实际内容(计数/等级/结论),不能是占位空串。"""
    for step in _build_reasoning_chain(_fake_result()):
        assert step["step"], "缺少步骤名"
        assert step["detail"], f"{step['node']} 这一步没有内容"
        assert step["detail"].strip()


def test_chain_reports_real_counts():
    """链上的数字必须来自真实结果,不能写死。"""
    chain = {s["node"]: s["detail"] for s in _build_reasoning_chain(_fake_result())}
    assert "3 种药物" in chain["parse"]
    assert "2 条相互作用" in chain["detect"]
    assert "2 条安全规则" in chain["rules"]
    assert "1 条禁忌判定" in chain["rules"]
    assert "critical" in chain["assess"]
    assert "1 种药物" in chain["recommend"]


def test_chain_survives_empty_result():
    """解析完全失败时也要给出六步(说明为什么空),而不是崩掉或返回 []。"""
    empty = _fake_result(
        prescription=Prescription(),
        drug_names=[],
        interactions=[],
        contraindications=[],
        rule_risks=[],
        risk_assessment=RiskAssessment(overall_risk="unknown"),
        alternatives=None,
        report="",
        patient={},
    )
    chain = _build_reasoning_chain(empty)
    assert len(chain) == 6
    details = {s["node"]: s["detail"] for s in chain}
    assert "未从处方文本中识别出药物" in details["parse"]
    assert "未命中" in details["detect"]
    assert "未触发替代方案分支" in details["recommend"]


def test_chain_handles_plain_dict_result():
    """兼容 dict / 对象两种取值(项目里两种都出现过)。"""
    chain = _build_reasoning_chain(
        {
            "drug_names": ["华法林"],
            "interactions": [],
            "rule_risks": [],
            "contraindications": [],
            "report": "x",
        }
    )
    assert len(chain) == 6


# ---------- API 层:字段真的被返回了 ----------

def test_raw_response_includes_reasoning_chain():
    """光有函数没用 —— 必须确认它被挂进了 API 响应。"""
    resp = _build_raw_response(_fake_result())
    assert "reasoning_chain" in resp
    assert len(resp["reasoning_chain"]) == 6


def test_raw_response_chain_detail_is_string():
    """前端直接 esc() 渲染,detail 必须是字符串(不能塞 dict 进去)。"""
    for step in _build_raw_response(_fake_result())["reasoning_chain"]:
        assert isinstance(step["detail"], str)
        assert isinstance(step["step"], str)


def test_long_summary_is_truncated():
    """摘要过长要截断,否则推理链会把整篇报告贴进去。"""
    long_text = "很长的结论。" * 100
    r = _fake_result(risk_assessment=RiskAssessment(overall_risk="high", summary=long_text))
    detail = {s["node"]: s["detail"] for s in _build_reasoning_chain(r)}["assess"]
    assert len(detail) < 260
    assert detail.endswith("…")
