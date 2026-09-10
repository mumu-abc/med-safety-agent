"""
评估闭环引擎 — 批量评测 + 回归检测 + 持久化。

评测流程：
  1. run_evaluation() 遍历标注用例
  2. 对每条用例运行图谱+规则检测
  3. 计算 F1/Precision/Recall
  4. 存入 SQLite，与历史基线对比
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── 评测用例（从 test_eval.py 提取核心子集）────────────────

QUICK_CASES = [
    # ── 高风险:多药联用 ──
    {"id": "H001", "desc": "华法林+阿司匹林+布洛芬,65岁", "drugs": ["华法林", "阿司匹林", "布洛芬"],
     "patient": {"age": 65, "gender": "男", "conditions": ["冠心病"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H002", "desc": "华法林+氯吡格雷,70岁", "drugs": ["华法林", "氯吡格雷"],
     "patient": {"age": 70, "gender": "男", "conditions": ["房颤"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},
    {"id": "H003", "desc": "地西泮+吗啡,80岁", "drugs": ["地西泮", "吗啡"],
     "patient": {"age": 80, "gender": "男", "conditions": ["疼痛"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H004", "desc": "氟西汀+利奈唑胺", "drugs": ["氟西汀", "利奈唑胺"],
     "patient": {"age": 45, "gender": "女", "conditions": ["抑郁症"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H009", "desc": "昂丹司琼+氟哌啶醇(QT叠加)", "drugs": ["昂丹司琼", "氟哌啶醇"],
     "patient": {"age": 55, "gender": "男", "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H010", "desc": "华法林+阿司匹林(双联抗栓)", "drugs": ["华法林", "阿司匹林"],
     "patient": {"age": 65, "gender": "男", "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── 高风险:特殊人群 ──
    {"id": "H005", "desc": "华法林+孕妇", "drugs": ["华法林"],
     "patient": {"age": 28, "gender": "女", "conditions": [], "pregnancy": "yes",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H006", "desc": "环丙沙星+儿童", "drugs": ["环丙沙星"],
     "patient": {"age": 10, "gender": "男", "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "H007", "desc": "二甲双胍+肾功能不全", "drugs": ["二甲双胍"],
     "patient": {"age": 70, "gender": "男", "conditions": ["糖尿病"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "impaired", "allergies": []},
     "expected_risk": "high"},
    {"id": "H008", "desc": "华法林+肝功能不全", "drugs": ["华法林"],
     "patient": {"age": 60, "gender": "男", "conditions": [], "pregnancy": "no",
                 "liver_function": "impaired", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},

    # ── 安全处方 ──
    {"id": "M001", "desc": "氨氯地平+单药,40岁", "drugs": ["氨氯地平"],
     "patient": {"age": 40, "gender": "男", "conditions": ["高血压"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "safe"},
    {"id": "M002", "desc": "对乙酰氨基酚+单药,30岁", "drugs": ["对乙酰氨基酚"],
     "patient": {"age": 30, "gender": "女", "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "safe"},
    {"id": "M003", "desc": "阿莫西林+氨溴索(普通感冒)", "drugs": ["阿莫西林", "氨溴索"],
     "patient": {"age": 30, "gender": "女", "conditions": ["上呼吸道感染"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "safe"},
    {"id": "M004", "desc": "二甲双胍+氨氯地平(糖尿病+高血压)", "drugs": ["二甲双胍", "氨氯地平"],
     "patient": {"age": 55, "gender": "男", "conditions": ["糖尿病", "高血压"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "safe"},

    # ── 过敏检测 ──
    {"id": "A001", "desc": "阿莫西林+青霉素过敏", "drugs": ["阿莫西林"],
     "patient": {"age": 35, "gender": "女", "conditions": [], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": ["青霉素"]},
     "expected_risk": "critical"},
    {"id": "A002", "desc": "头孢曲松+头孢过敏", "drugs": ["头孢曲松"],
     "patient": {"age": 40, "gender": "男", "conditions": ["肺炎"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": ["头孢"]},
     "expected_risk": "critical"},
    {"id": "A003", "desc": "布洛芬+NSAIDs过敏", "drugs": ["布洛芬"],
     "patient": {"age": 50, "gender": "女", "conditions": ["关节炎"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": ["NSAIDs"]},
     "expected_risk": "critical"},

    # ── QT延长 ──
    {"id": "Q001", "desc": "红霉素+环丙沙星(QT叠加)", "drugs": ["红霉素", "环丙沙星"],
     "patient": {"age": 60, "gender": "男", "conditions": ["肺炎"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "Q002", "desc": "西酞普兰单药(QT风险)", "drugs": ["西酞普兰"],
     "patient": {"age": 35, "gender": "女", "conditions": ["抑郁症"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── CNS抑制 ──
    {"id": "C001", "desc": "芬太尼+阿普唑仑(FDA黑框)", "drugs": ["芬太尼", "阿普唑仑"],
     "patient": {"age": 70, "gender": "男", "conditions": ["疼痛", "焦虑"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "C002", "desc": "曲马多+地西泮(CNS叠加)", "drugs": ["曲马多", "地西泮"],
     "patient": {"age": 65, "gender": "女", "conditions": ["疼痛"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},

    # ── 5-HT综合征 ──
    {"id": "S001", "desc": "氟西汀+司来吉兰(SSRI+MAO-B)", "drugs": ["氟西汀", "司来吉兰"],
     "patient": {"age": 55, "gender": "男", "conditions": ["帕金森", "抑郁"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},
    {"id": "S002", "desc": "舍曲林+曲马多(5-HT叠加)", "drugs": ["舍曲林", "曲马多"],
     "patient": {"age": 45, "gender": "女", "conditions": ["抑郁症", "疼痛"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── 老年人多重风险 ──
    {"id": "E001", "desc": "地西泮+布洛芬+地高辛(老年人多药)", "drugs": ["地西泮", "布洛芬", "地高辛"],
     "patient": {"age": 78, "gender": "男", "conditions": ["房颤", "关节炎"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "E002", "desc": "阿司匹林+布洛芬(老年人)", "drugs": ["阿司匹林", "布洛芬"],
     "patient": {"age": 72, "gender": "女", "conditions": ["冠心病"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── 孕妇复合场景 ──
    {"id": "P001", "desc": "异维A酸+孕妇(极高致畸)", "drugs": ["异维A酸"],
     "patient": {"age": 25, "gender": "女", "conditions": ["痤疮"], "pregnancy": "yes",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "P002", "desc": "布洛芬+孕晚期", "drugs": ["布洛芬"],
     "patient": {"age": 30, "gender": "女", "conditions": ["疼痛"], "pregnancy": "yes",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── 出血风险组合 ──
    {"id": "B001", "desc": "华法林+阿司匹林+布洛芬(三联出血)", "drugs": ["华法林", "阿司匹林", "布洛芬"],
     "patient": {"age": 68, "gender": "男", "conditions": ["房颤", "冠心病"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "B002", "desc": "利伐沙班+氯吡格雷(双联抗凝)", "drugs": ["利伐沙班", "氯吡格雷"],
     "patient": {"age": 65, "gender": "男", "conditions": ["房颤"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "high"},

    # ── 儿童边界 ──
    {"id": "K001", "desc": "阿司匹林+儿童(Reye综合征)", "drugs": ["阿司匹林"],
     "patient": {"age": 12, "gender": "男", "conditions": ["发热"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
    {"id": "K002", "desc": "多西环素+8岁以下", "drugs": ["多西环素"],
     "patient": {"age": 6, "gender": "女", "conditions": ["感染"], "pregnancy": "no",
                 "liver_function": "normal", "renal_function": "normal", "allergies": []},
     "expected_risk": "critical"},
]

# ── 风险等级映射 ──────────────────────────────────────────

RISK_LEVELS = {"critical": 4, "high": 3, "medium": 2, "low": 1, "safe": 0}


def _detect_risk_level(case: dict) -> str:
    """用图谱+规则检测风险等级。"""
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    from app.rules.safety_rules import run_all_rules

    build_graph_from_data()

    drugs = []
    for name in case["drugs"]:
        d = get_drug_by_name(name)
        if d:
            drugs.append(d)
        else:
            drugs.append({"id": name.lower(), "name": name})

    drug_ids = [d["id"] for d in drugs]
    interactions = find_interactions(drug_ids)
    contraindications = []
    for d in drugs:
        conds = case["patient"].get("conditions", [])
        c = find_contraindications(d["id"], conds)
        contraindications.extend(c)

    risks = run_all_rules(drugs, case["patient"])

    # 聚合判断
    all_severities = set()
    for i in interactions:
        all_severities.add(i.get("severity", "medium"))
    for c in contraindications:
        all_severities.add(c.get("severity", "high"))
    for r in risks:
        all_severities.add(r.get("severity", "medium"))

    if "critical" in all_severities:
        return "critical"
    elif "high" in all_severities:
        return "high"
    elif "medium" in all_severities:
        return "medium"
    elif "low" in all_severities:
        return "low"
    return "safe"


def _binary_label(risk: str) -> str:
    """二分类标签：critical/high → positive, 其余 → negative。"""
    return "positive" if risk in ("critical", "high") else "negative"


# ── 评测函数 ──────────────────────────────────────────────

def run_evaluation(cases: Optional[list[dict]] = None) -> dict:
    """
    批量评测。

    Returns:
        {
            "run_id": str,
            "timestamp": str,
            "cases": [{case_id, desc, expected, detected, correct, binary_expected, binary_detected, binary_correct}],
            "metrics": {accuracy, precision, recall, f1, tp, fp, fn, tn, total, exact_match},
        }
    """
    cases = cases or QUICK_CASES
    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    case_results = []

    for case in cases:
        try:
            detected = _detect_risk_level(case)
            expected = case["expected_risk"]
            binary_exp = _binary_label(expected)
            binary_det = _binary_label(detected)

            case_results.append({
                "case_id": case["id"],
                "desc": case["desc"],
                "expected": expected,
                "detected": detected,
                "correct": expected == detected,
                "binary_expected": binary_exp,
                "binary_detected": binary_det,
                "binary_correct": binary_exp == binary_det,
            })
        except Exception as e:
            logger.error(f"评测 {case['id']} 失败: {e}")
            case_results.append({
                "case_id": case["id"], "desc": case["desc"],
                "expected": case["expected_risk"], "detected": "error",
                "correct": False, "binary_expected": _binary_label(case["expected_risk"]),
                "binary_detected": "negative", "binary_correct": False,
            })

    # 计算二分类指标
    tp = sum(1 for r in case_results if r["binary_expected"] == "positive" and r["binary_detected"] == "positive")
    fp = sum(1 for r in case_results if r["binary_expected"] == "negative" and r["binary_detected"] == "positive")
    fn = sum(1 for r in case_results if r["binary_expected"] == "positive" and r["binary_detected"] == "negative")
    tn = sum(1 for r in case_results if r["binary_expected"] == "negative" and r["binary_detected"] == "negative")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    metrics = {
        "accuracy": round((tp + tn) / len(case_results), 4) if case_results else 0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "total": len(case_results),
        "exact_match": sum(1 for r in case_results if r["correct"]),
    }

    result = {
        "run_id": run_id,
        "run_name": f"评测 {datetime.now().strftime('%m-%d %H:%M')}",
        "timestamp": datetime.now().isoformat(),
        "cases": case_results,
        "metrics": metrics,
    }

    logger.info(
        f"📊 评测完成: F1={f1:.1%} P={precision:.1%} R={recall:.1%} "
        f"准确匹配={metrics['exact_match']}/{metrics['total']}"
    )

    return result


# ── 回归检测 ──────────────────────────────────────────────

def detect_regressions(current: dict, baseline: Optional[dict] = None, threshold: float = 0.05) -> dict:
    """
    对比当前评测与基线，检测回归。

    Args:
        current: 当前评测结果
        baseline: 基线评测结果
        threshold: F1 下降阈值（超过则标记为回归）

    Returns:
        {"has_regression": bool, "regressions": [...], "improvements": [...], "metric_delta": {...}}
    """
    if baseline is None:
        try:
            from app.database import db
            latest = db.get_latest_eval_run()
            if latest:
                baseline = db.get_eval_run(latest["id"])
        except Exception as e:
            logger.warning(f"获取基线数据失败: {e}")

    if not baseline:
        return {"has_regression": False, "regressions": [], "improvements": [], "metric_delta": {},
                "message": "无基线数据"}

    curr_m = current.get("metrics", {})
    base_m = baseline.get("metrics", {})

    metric_delta = {}
    regressions = []
    improvements = []

    for key in ("f1", "precision", "recall", "accuracy"):
        delta = curr_m.get(key, 0) - base_m.get(key, 0)
        metric_delta[key] = round(delta, 4)
        if delta < -threshold:
            regressions.append({"metric": key, "current": curr_m[key], "baseline": base_m[key], "drop": abs(delta)})
        elif delta > threshold:
            improvements.append({"metric": key, "current": curr_m[key], "baseline": base_m[key], "gain": delta})

    # 用例级别对比
    baseline_cases = {c["case_id"]: c for c in baseline.get("cases", [])}
    for case in current.get("cases", []):
        cid = case["case_id"]
        if cid in baseline_cases and case["correct"] and not baseline_cases[cid]["correct"]:
            improvements.append({"case_id": cid, "desc": case["desc"], "type": "newly_correct"})
        elif cid in baseline_cases and not case["correct"] and baseline_cases[cid]["correct"]:
            regressions.append({"case_id": cid, "desc": case["desc"], "type": "newly_incorrect"})

    return {
        "has_regression": len(regressions) > 0,
        "regressions": regressions,
        "improvements": improvements,
        "metric_delta": metric_delta,
    }
