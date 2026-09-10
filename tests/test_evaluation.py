"""
评估闭环测试 — 评测运行、指标计算、回归检测、持久化。
"""

import pytest
import tempfile
import os
from pathlib import Path


def test_quick_cases_count():
    """快速评测用例应 >= 10 条"""
    from app.evaluation import QUICK_CASES
    assert len(QUICK_CASES) >= 10


def test_quick_cases_structure():
    """每条用例必须包含必要字段"""
    from app.evaluation import QUICK_CASES
    for case in QUICK_CASES:
        assert "id" in case
        assert "drugs" in case
        assert "expected_risk" in case
        assert case["expected_risk"] in ("critical", "high", "medium", "low", "safe")


def test_run_evaluation_metrics():
    """评测应返回有效指标"""
    from app.evaluation import run_evaluation
    result = run_evaluation()
    m = result["metrics"]
    assert m["total"] >= 10
    assert 0 <= m["f1"] <= 1
    assert 0 <= m["precision"] <= 1
    assert 0 <= m["recall"] <= 1
    assert m["tp"] + m["fp"] + m["fn"] + m["tn"] == m["total"]


def test_run_evaluation_f1():
    """图谱+规则 F1 应 >= 80%"""
    from app.evaluation import run_evaluation
    result = run_evaluation()
    assert result["metrics"]["f1"] >= 0.8, f"F1 过低: {result['metrics']['f1']:.1%}"


def test_run_evaluation_recall():
    """召回率应 >= 90%"""
    from app.evaluation import run_evaluation
    result = run_evaluation()
    assert result["metrics"]["recall"] >= 0.9, f"召回率过低: {result['metrics']['recall']:.1%}"


def test_run_evaluation_case_results():
    """每条用例应有完整结果"""
    from app.evaluation import run_evaluation
    result = run_evaluation()
    for case in result["cases"]:
        assert "case_id" in case
        assert "expected" in case
        assert "detected" in case
        assert "correct" in case
        assert "binary_correct" in case


def test_detect_regressions_no_baseline():
    """无基线时应返回无回归"""
    from app.evaluation import detect_regressions
    current = {"metrics": {"f1": 0.9, "precision": 0.9, "recall": 0.9, "accuracy": 0.9}, "cases": []}
    result = detect_regressions(current, baseline=None)
    assert result["has_regression"] is False


def test_detect_regressions_with_baseline():
    """有基线时应正确检测回归和改进"""
    from app.evaluation import detect_regressions
    current = {
        "metrics": {"f1": 0.85, "precision": 0.80, "recall": 0.90, "accuracy": 0.85},
        "cases": [
            {"case_id": "H001", "desc": "test", "correct": True},
            {"case_id": "H002", "desc": "test", "correct": False},
        ],
    }
    baseline = {
        "metrics": {"f1": 0.95, "precision": 0.95, "recall": 0.95, "accuracy": 0.95},
        "cases": [
            {"case_id": "H001", "desc": "test", "correct": False},
            {"case_id": "H002", "desc": "test", "correct": True},
        ],
    }
    result = detect_regressions(current, baseline, threshold=0.05)
    # F1 从 0.95 降到 0.85 → 回归
    assert result["has_regression"] is True
    assert any(r["metric"] == "f1" for r in result["regressions"])
    # H001 从错→对 → 改进
    assert any(r.get("case_id") == "H001" and r.get("type") == "newly_correct" for r in result["improvements"])
    # H002 从对→错 → 回归
    assert any(r.get("case_id") == "H002" and r.get("type") == "newly_incorrect" for r in result["regressions"])


def test_binary_label_mapping():
    """风险等级二分类映射"""
    from app.evaluation import _binary_label
    assert _binary_label("critical") == "positive"
    assert _binary_label("high") == "positive"
    assert _binary_label("medium") == "negative"
    assert _binary_label("low") == "negative"
    assert _binary_label("safe") == "negative"


def test_allergen_detection():
    """过敏交叉检查应能检出"""
    from app.evaluation import _detect_risk_level
    case = {
        "drugs": ["阿莫西林"],
        "patient": {"age": 35, "gender": "女", "conditions": [], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal", "allergies": ["青霉素"]},
        "expected_risk": "critical",
    }
    risk = _detect_risk_level(case)
    assert risk in ("critical", "high"), f"过敏未检出: {risk}"


def test_qt_stacking_detection():
    """QT叠加应被检出"""
    from app.evaluation import _detect_risk_level
    case = {
        "drugs": ["昂丹司琼", "氟哌啶醇"],
        "patient": {"age": 55, "gender": "男", "conditions": [], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal", "allergies": []},
        "expected_risk": "critical",
    }
    risk = _detect_risk_level(case)
    assert risk in ("critical", "high"), f"QT叠加未检出: {risk}"


def test_cns_opioid_benzo_detection():
    """阿片+苯二氮卓应被检出"""
    from app.evaluation import _detect_risk_level
    case = {
        "drugs": ["吗啡", "地西泮"],
        "patient": {"age": 80, "gender": "男", "conditions": [], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal", "allergies": []},
        "expected_risk": "critical",
    }
    risk = _detect_risk_level(case)
    assert risk in ("critical", "high"), f"CNS抑制未检出: {risk}"


# ── 数据库集成测试 ─────────────────────────────────────────

def test_eval_database_save_and_retrieve():
    """评测结果的存储和读取"""
    from app.database import Database

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = Database.__new__(Database)
        db._local = type('Local', (), {})()
        import sqlite3
        db._local.conn = sqlite3.connect(db_path, check_same_thread=False)
        db._local.conn.row_factory = sqlite3.Row
        db._init_db()

        eval_result = {
            "run_id": "eval_test01",
            "run_name": "测试评测",
            "timestamp": "2026-01-01T00:00:00",
            "cases": [
                {"case_id": "H001", "desc": "测试", "expected": "critical",
                 "detected": "critical", "correct": True},
            ],
            "metrics": {
                "f1": 0.95, "precision": 0.9, "recall": 1.0,
                "accuracy": 0.95, "total": 1, "exact_match": 1,
                "tp": 1, "fp": 0, "fn": 0, "tn": 0,
            },
        }

        run_id = db.save_eval_run(eval_result)
        assert run_id == "eval_test01"

        runs = db.get_eval_runs()
        assert len(runs) == 1

        detail = db.get_eval_run("eval_test01")
        assert detail is not None
        assert len(detail["cases"]) == 1

        latest = db.get_latest_eval_run()
        assert latest is not None

        db.close()
    finally:
        import time
        time.sleep(0.1)
        try:
            os.unlink(db_path)
        except PermissionError:
            pass


def test_quick_cases_coverage():
    """评测用例应覆盖主要规则类别。"""
    from app.evaluation import QUICK_CASES
    ids = {c["id"] for c in QUICK_CASES}
    assert any(i.startswith("H") for i in ids)
    assert any(i.startswith("M") for i in ids)
    assert any(i.startswith("A") for i in ids)
    assert any(i.startswith("Q") for i in ids)
    assert any(i.startswith("C") for i in ids)


def test_quick_cases_all_have_required_fields():
    """所有用例必须有必需字段。"""
    from app.evaluation import QUICK_CASES
    for case in QUICK_CASES:
        assert "id" in case
        assert "desc" in case
        assert "drugs" in case
        assert "patient" in case
        assert "expected_risk" in case
        assert case["expected_risk"] in ("critical", "high", "medium", "low", "safe")


def test_quick_cases_at_least_30():
    """评测用例应不少于30个。"""
    from app.evaluation import QUICK_CASES
    assert len(QUICK_CASES) >= 30, f"评测用例不足30: {len(QUICK_CASES)}"
