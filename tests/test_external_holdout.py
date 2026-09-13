"""外部 holdout 数据集结构与基线质量测试(无 LLM)。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "eval_external_holdout.json"


def test_external_holdout_schema():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 50
    assert data["meta"]["description"]
    for c in cases:
        assert c["id"].startswith("EX-")
        assert c["drugs"]
        assert c["expected_risk"] in ("critical", "high", "medium", "low", "safe")
        assert c["source"]


def test_external_holdout_not_generated_from_project_ids_only():
    """holdout 应包含单药特殊人群与多药联用,不能全是图谱边的镜像。"""
    cases = json.loads(DATA.read_text(encoding="utf-8"))["cases"]
    multi = [c for c in cases if len(c["drugs"]) >= 2]
    single = [c for c in cases if len(c["drugs"]) == 1]
    assert multi and single
    # 至少有一部分 safe 负样本,防止全是高风险
    assert any(c["expected_risk"] == "safe" for c in cases)


def test_external_eval_runs():
    from scripts.eval_external_holdout import eval_graph_rules, load_cases, metrics

    results = eval_graph_rules(load_cases())
    m = metrics(results)
    assert m["n"] >= 25
    assert 0 <= m["f1"] <= 1
    # 外部集不应虚假饱和;若 F1=1.0 需人工复核是否标签过松
    # 这里只要求可运行,具体数值见 EXTERNAL_HOLDOUT_REPORT
