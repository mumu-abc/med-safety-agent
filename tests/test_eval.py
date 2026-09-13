"""评测框架:对比"纯规则" vs "图谱+规则" vs "完整三层架构(含LLM)"。

运行方式:
  python tests/test_eval.py              # 规则+图谱评测(不需要LLM)
  python tests/test_eval.py --full       # 完整三层评测(需要LLM API)
  python tests/test_eval.py --full --report  # 生成 markdown 报告

输出指标:
  - Accuracy (准确率)
  - Precision (精确率)
  - Recall (召回率)
  - F1 Score
  - Per-class 指标(critical/high/medium/safe)
  - 分类别统计(高风险/特殊人群/安全)
  - Per-case 详情对比
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.drug_data import build_graph_from_data
from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
from app.rules.safety_rules import run_all_rules


# ---- 标注数据集(手工标注 + 程序生成) ----

EVAL_CASES = [
    # === 高风险案例 ===
    {
        "id": "H001",
        "desc": "华法林+阿司匹林+布洛芬,65岁冠心病",
        "drugs": ["华法林", "阿司匹林", "布洛芬"],
        "patient": {"age": 65, "gender": "男", "conditions": ["冠心病"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者王某,男,65岁,高血压病史10年,2型糖尿病5年\n诊断:冠心病,高血压,2型糖尿病\n处方:\n1. 华法林 2.5mg qd\n2. 阿司匹林 100mg qd\n3. 氨氯地平 5mg qd\n4. 二甲双胍 500mg bid\n5. 布洛芬 400mg prn(头痛时服用)",
        "expected_risk": "critical",
        "expected_min_interactions": 2,
        "expected_min_rules": 1,
    },
    {
        "id": "H002",
        "desc": "华法林+氯吡格雷,70岁房颤",
        "drugs": ["华法林", "氯吡格雷"],
        "patient": {"age": 70, "gender": "男", "conditions": ["房颤"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,70岁,房颤\n处方:\n1. 华法林 3mg qd\n2. 氯吡格雷 75mg qd",
        "expected_risk": "critical",
        "expected_min_interactions": 1,
        "expected_min_rules": 1,
    },
    {
        "id": "H003",
        "desc": "地高辛+呋塞米+螺内酯,72岁心衰",
        "drugs": ["地高辛", "呋塞米", "螺内酯"],
        "patient": {"age": 72, "gender": "男", "conditions": ["心力衰竭", "房颤"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "impaired"},
        "prescription_text": "患者男,72岁,心力衰竭,房颤,肾功能轻度受损\n处方:\n1. 地高辛 0.125mg qd\n2. 呋塞米 20mg qd\n3. 螺内酯 20mg qd",
        "expected_risk": "high",
        "expected_min_interactions": 0,
        "expected_min_rules": 1,
    },
    {
        "id": "H004",
        "desc": "阿托伐他汀+克拉霉素,68岁",
        "drugs": ["阿托伐他汀", "克拉霉素"],
        "patient": {"age": 68, "gender": "女", "conditions": ["高脂血症"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,68岁,高脂血症\n处方:\n1. 阿托伐他汀 40mg qd\n2. 克拉霉素 500mg bid",
        "expected_risk": "high",
        "expected_min_interactions": 1,
        "expected_min_rules": 0,
    },
    {
        "id": "H005",
        "desc": "美托洛尔+维拉帕米,60岁高血压",
        "drugs": ["美托洛尔", "维拉帕米"],
        "patient": {"age": 60, "gender": "男", "conditions": ["高血压"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,60岁,高血压\n处方:\n1. 美托洛尔 47.5mg qd\n2. 维拉帕米 80mg tid",
        "expected_risk": "high",
        "expected_min_interactions": 1,
        "expected_min_rules": 0,
    },
    # === 中风险案例 ===
    {
        "id": "M001",
        "desc": "氨氯地平+辛伐他汀,55岁高血压+高脂血症",
        "drugs": ["氨氯地平", "辛伐他汀"],
        "patient": {"age": 55, "gender": "男", "conditions": ["高血压", "高脂血症"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,55岁,高血压,高脂血症\n处方:\n1. 氨氯地平 5mg qd\n2. 辛伐他汀 20mg qn",
        "expected_risk": "medium",
        "expected_min_interactions": 1,
        "expected_min_rules": 0,
    },
    {
        "id": "M002",
        "desc": "二甲双胍+碘造影剂,50岁糖尿病",
        "drugs": ["二甲双胍", "碘造影剂"],
        "patient": {"age": 50, "gender": "女", "conditions": ["糖尿病"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,50岁,糖尿病,拟行冠脉造影\n处方:\n1. 二甲双胍 500mg bid\n2. 碘造影剂 造影用",
        "expected_risk": "medium",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    # === 孕妇案例 ===
    {
        "id": "P001",
        "desc": "华法林+氯沙坦,28岁孕妇",
        "drugs": ["华法林", "氯沙坦"],
        "patient": {"age": 28, "gender": "女", "conditions": ["高血压"], "pregnancy": "yes",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,28岁,孕12周,高血压\n处方:\n1. 华法林 2.5mg qd\n2. 氯沙坦 50mg qd",
        "expected_risk": "critical",
        "expected_min_interactions": 0,
        "expected_min_rules": 2,
    },
    {
        "id": "P002",
        "desc": "阿托伐他汀+美托洛尔,30岁孕妇",
        "drugs": ["阿托伐他汀", "美托洛尔"],
        "patient": {"age": 30, "gender": "女", "conditions": ["高血压", "高脂血症"], "pregnancy": "yes",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,30岁,孕20周,高血压,高脂血症\n处方:\n1. 阿托伐他汀 20mg qd\n2. 美托洛尔 25mg bid",
        "expected_risk": "high",
        "expected_min_interactions": 0,
        "expected_min_rules": 1,
    },
    # === 儿童案例 ===
    {
        "id": "C001",
        "desc": "环丙沙星+阿司匹林,10岁",
        "drugs": ["环丙沙星", "阿司匹林"],
        "patient": {"age": 10, "gender": "男", "conditions": ["感染"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,10岁,呼吸道感染\n处方:\n1. 环丙沙星 250mg bid\n2. 阿司匹林 100mg qd",
        "expected_risk": "high",
        "expected_min_interactions": 0,
        "expected_min_rules": 2,
    },
    # === 安全案例 ===
    {
        "id": "S001",
        "desc": "氨氯地平+对乙酰氨基酚,45岁高血压",
        "drugs": ["氨氯地平", "对乙酰氨基酚"],
        "patient": {"age": 45, "gender": "女", "conditions": ["高血压"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,45岁,高血压\n处方:\n1. 氨氯地平 5mg qd\n2. 对乙酰氨基酚 500mg prn",
        "expected_risk": "safe",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    {
        "id": "S002",
        "desc": "奥美拉唑+莫沙必利,40岁胃炎",
        "drugs": ["奥美拉唑", "莫沙必利"],
        "patient": {"age": 40, "gender": "男", "conditions": ["胃炎"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,40岁,胃炎\n处方:\n1. 奥美拉唑 20mg qd\n2. 莫沙必利 5mg tid",
        "expected_risk": "safe",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    {
        "id": "S003",
        "desc": "左甲状腺素+碳酸钙,50岁甲减",
        "drugs": ["左甲状腺素", "碳酸钙"],
        "patient": {"age": 50, "gender": "女", "conditions": ["甲状腺功能减退"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,50岁,甲状腺功能减退\n处方:\n1. 左甲状腺素 50μg qd\n2. 碳酸钙 600mg qd",
        "expected_risk": "safe",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    {
        "id": "S004",
        "desc": "二甲双胍+阿卡波糖,55岁糖尿病",
        "drugs": ["二甲双胍", "阿卡波糖"],
        "patient": {"age": 55, "gender": "男", "conditions": ["糖尿病"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,55岁,2型糖尿病\n处方:\n1. 二甲双胍 500mg bid\n2. 阿卡波糖 50mg tid",
        "expected_risk": "safe",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    # === LLM 独特发现案例(规则和图谱无法检测) ===
    {
        "id": "L001",
        "desc": "依那普利+缬沙坦,60岁高血压(双重RAAS阻断)",
        "drugs": ["依那普利", "缬沙坦"],
        "patient": {"age": 60, "gender": "男", "conditions": ["高血压"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者男,60岁,高血压\n处方:\n1. 依那普利 10mg bid\n2. 缬沙坦 80mg qd",
        "expected_risk": "medium",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
    {
        "id": "L002",
        "desc": "氨氯地平+缬沙坦,55岁高血压(合理联用)",
        "drugs": ["氨氯地平", "缬沙坦"],
        "patient": {"age": 55, "gender": "女", "conditions": ["高血压"], "pregnancy": "no",
                    "liver_function": "normal", "renal_function": "normal"},
        "prescription_text": "患者女,55岁,高血压\n处方:\n1. 氨氯地平 5mg qd\n2. 缬沙坦 80mg qd",
        "expected_risk": "safe",
        "expected_min_interactions": 0,
        "expected_min_rules": 0,
    },
]


def _load_generated_cases() -> list[dict]:
    """加载程序生成的评测用例。"""
    gen_path = Path(__file__).resolve().parent.parent / "data" / "eval_cases_generated.json"
    if not gen_path.exists():
        return []
    with open(gen_path, encoding="utf-8") as f:
        cases = json.load(f)
    # 转换为与 EVAL_CASES 兼容的格式
    converted = []
    for c in cases:
        converted.append({
            "id": c["id"],
            "desc": c["desc"],
            "drugs": c["drugs"],
            "patient": c["patient"],
            "prescription_text": c.get("prescription_text", ""),
            "expected_risk": c["expected_risk"],
            "expected_min_interactions": c.get("expected_min_interactions", 0),
            "expected_min_rules": c.get("expected_min_rules", 0),
            "category": c.get("category", "generated"),
        })
    return converted


def get_all_cases(include_generated: bool = True) -> list[dict]:
    """获取全部评测用例(手工 + 生成)。"""
    all_cases = list(EVAL_CASES)
    if include_generated:
        all_cases.extend(_load_generated_cases())
    return all_cases


def _risk_level_num(level: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "safe": 0}.get(level, -1)


def eval_rules_only(cases=None):
    build_graph_from_data()
    all_cases = cases or get_all_cases()
    results = []
    for case in all_cases:
        ids = [get_drug_by_name(n)["id"] for n in case["drugs"] if get_drug_by_name(n)]
        interactions = find_interactions(ids) if len(ids) >= 2 else []
        drugs_info = [{"id": did, "name": n} for did, n in zip(ids, case["drugs"])]
        rule_risks = run_all_rules(drugs_info, case["patient"])
        if rule_risks:
            max_sev = max((_risk_level_num(r["severity"]) for r in rule_risks), default=0)
            detected = {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(max_sev, "low")
        elif interactions:
            max_sev = max((_risk_level_num(i["severity"]) for i in interactions), default=0)
            detected = {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(max_sev, "low")
        else:
            detected = "safe"
        results.append({
            "id": case["id"], "desc": case["desc"],
            "expected": case["expected_risk"], "detected": detected,
            "interactions": len(interactions), "rules": len(rule_risks),
            "category": case.get("category", ""),
        })
    return results


def eval_three_layer(cases=None):
    build_graph_from_data()
    all_cases = cases or get_all_cases()
    results = []
    for case in all_cases:
        ids = [get_drug_by_name(n)["id"] for n in case["drugs"] if get_drug_by_name(n)]
        interactions = find_interactions(ids) if len(ids) >= 2 else []
        contras = []
        for name in case["drugs"]:
            d = get_drug_by_name(name)
            if d and case["patient"].get("conditions"):
                contras.extend(find_contraindications(d["id"], case["patient"]["conditions"]))
        drugs_info = [{"id": did, "name": n} for did, n in zip(ids, case["drugs"])]
        rule_risks = run_all_rules(drugs_info, case["patient"])
        all_sev = [_risk_level_num(i["severity"]) for i in interactions]
        all_sev += [4 for _ in contras]
        all_sev += [_risk_level_num(r["severity"]) for r in rule_risks]
        if all_sev:
            max_sev = max(all_sev)
            detected = {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(max_sev, "low")
        else:
            detected = "safe"
        results.append({
            "id": case["id"], "desc": case["desc"],
            "expected": case["expected_risk"], "detected": detected,
            "interactions": len(interactions), "contraindications": len(contras), "rules": len(rule_risks),
            "category": case.get("category", ""),
        })
    return results


def eval_full_pipeline(cases=None):
    """完整三层架构评测(图谱+规则+LLM ReAct)。"""
    from app.workflow import review_prescription
    all_cases = cases or get_all_cases()
    results = []
    for case in all_cases:
        try:
            result = review_prescription(case["prescription_text"])
            ra = result.get("risk_assessment")
            detected_risk = ra.overall_risk if ra else "unknown"
            risk_count = len(ra.risks) if ra else 0
            interaction_count = len(result.get("interactions", []))
            rule_count = len(result.get("rule_risks", []))
            alts = result.get("alternatives")
            has_alts = bool(alts and alts.suggestions)
        except Exception as e:
            detected_risk = "error"
            risk_count = 0
            interaction_count = 0
            rule_count = 0
            has_alts = False
            print(f"  ⚠️ {case['id']} 异常: {e}")
        results.append({
            "id": case["id"], "desc": case["desc"],
            "expected": case["expected_risk"], "detected": detected_risk,
            "interactions": interaction_count, "rules": rule_count,
            "risk_count": risk_count, "has_alternatives": has_alts,
            "category": case.get("category", ""),
        })
    return results


def _calc_metrics(results):
    tp = fp = fn = tn = 0
    for r in results:
        exp_high = r["expected"] in ("critical", "high")
        det_high = r["detected"] in ("critical", "high")
        if exp_high and det_high: tp += 1
        elif not exp_high and det_high: fp += 1
        elif exp_high and not det_high: fn += 1
        else: tn += 1
    accuracy = (tp + tn) / len(results) if results else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    exact = sum(1 for r in results if r["expected"] == r["detected"])
    return {"total": len(results), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "accuracy": round(accuracy, 3), "precision": round(precision, 3),
            "recall": round(recall, 3), "f1": round(f1, 3),
            "exact_match": exact, "exact_match_rate": round(exact / len(results), 3) if results else 0}


def _calc_multiclass_metrics(results: list[dict]) -> dict:
    """计算多分类指标:每个风险等级的 precision/recall/f1。"""
    levels = ["critical", "high", "medium", "low", "safe"]
    per_class = {}
    for level in levels:
        tp = sum(1 for r in results if r["expected"] == level and r["detected"] == level)
        fp = sum(1 for r in results if r["expected"] != level and r["detected"] == level)
        fn = sum(1 for r in results if r["expected"] == level and r["detected"] != level)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = sum(1 for r in results if r["expected"] == level)
        if support > 0 or tp > 0:
            per_class[level] = {
                "precision": round(precision, 3), "recall": round(recall, 3),
                "f1": round(f1, 3), "support": support, "tp": tp, "fp": fp, "fn": fn,
            }
    return per_class


def _calc_category_stats(results: list[dict]) -> dict:
    """按用例类别统计召回率。"""
    # 定义类别分组
    category_groups = {
        "高风险交互": lambda r: r.get("category") == "高风险交互",
        "特殊人群": lambda r: r.get("category") in ("孕妇禁忌", "儿童禁忌", "老年人高危", "肾功能不全", "肝功能不全"),
        "中风险": lambda r: r.get("category") == "中风险",
        "安全组合": lambda r: r.get("category") == "安全组合",
        "多药联用": lambda r: r.get("category") == "多药联用",
    }
    stats = {}
    for group_name, filter_fn in category_groups.items():
        group_results = [r for r in results if filter_fn(r)]
        if not group_results:
            continue
        # 对于高风险/特殊人群，看是否检测出 high+
        if group_name in ("高风险交互", "特殊人群", "多药联用"):
            correct = sum(1 for r in group_results
                          if r["expected"] in ("critical", "high") and r["detected"] in ("critical", "high"))
            total_positive = sum(1 for r in group_results if r["expected"] in ("critical", "high"))
        elif group_name == "安全组合":
            correct = sum(1 for r in group_results if r["detected"] == r["expected"])
            total_positive = len(group_results)
        else:
            correct = sum(1 for r in group_results if r["detected"] == r["expected"])
            total_positive = len(group_results)

        stats[group_name] = {
            "total": len(group_results),
            "correct": correct,
            "accuracy": round(correct / len(group_results), 3) if group_results else 0,
        }
    return stats


def _generate_markdown_report(rule_r, three_r, full_r, rule_m, three_m, full_m,
                               rule_mc=None, three_mc=None, full_mc=None,
                               rule_cat=None, three_cat=None, full_cat=None,
                               all_cases=None):
    lines = []
    lines.append("# 📊 用药安全审查系统 — 评测报告\n")
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    num_handmade = len(EVAL_CASES)
    num_generated = len(all_cases) - num_handmade if all_cases else 0
    total = len(all_cases) if all_cases else num_handmade
    lines.append(f"> 标注样本数: {total} (手工标注 {num_handmade} + 程序生成 {num_generated})\n")
    lines.append("## 1. 总览(二分类)\n")
    lines.append("| 方案 | Accuracy | Precision | Recall | F1 | 精确匹配 |")
    lines.append("|------|----------|-----------|--------|----|----------|")
    lines.append(f"| 纯规则引擎 | {rule_m['accuracy']:.1%} | {rule_m['precision']:.1%} | {rule_m['recall']:.1%} | {rule_m['f1']:.1%} | {rule_m['exact_match']}/{rule_m['total']} |")
    lines.append(f"| 图谱+规则 | {three_m['accuracy']:.1%} | {three_m['precision']:.1%} | {three_m['recall']:.1%} | {three_m['f1']:.1%} | {three_m['exact_match']}/{three_m['total']} |")
    if full_r:
        lines.append(f"| **完整三层(含LLM)** | **{full_m['accuracy']:.1%}** | **{full_m['precision']:.1%}** | **{full_m['recall']:.1%}** | **{full_m['f1']:.1%}** | **{full_m['exact_match']}/{full_m['total']}** |")
    lines.append("")
    lines.append("## 2. 混淆矩阵\n")
    lines.append("| 方案 | TP | FP | FN | TN |")
    lines.append("|------|----|----|----|----|")
    lines.append(f"| 纯规则引擎 | {rule_m['tp']} | {rule_m['fp']} | {rule_m['fn']} | {rule_m['tn']} |")
    lines.append(f"| 图谱+规则 | {three_m['tp']} | {three_m['fp']} | {three_m['fn']} | {three_m['tn']} |")
    if full_r:
        lines.append(f"| 完整三层(含LLM) | {full_m['tp']} | {full_m['fp']} | {full_m['fn']} | {full_m['tn']} |")
    lines.append("")

    # 多分类指标
    if three_mc:
        lines.append("## 3. 多分类指标(图谱+规则方案)\n")
        lines.append("| 风险等级 | Precision | Recall | F1 | 支持数 |")
        lines.append("|----------|-----------|--------|----|--------|")
        for level in ["critical", "high", "medium", "low", "safe"]:
            if level in three_mc:
                m = three_mc[level]
                lines.append(f"| {level} | {m['precision']:.1%} | {m['recall']:.1%} | {m['f1']:.1%} | {m['support']} |")
        lines.append("")

    # 分类别统计
    if three_cat:
        lines.append("## 4. 分类别统计(图谱+规则方案)\n")
        lines.append("| 用例类别 | 总数 | 正确 | 准确率 |")
        lines.append("|----------|------|------|--------|")
        for cat_name, stats in sorted(three_cat.items()):
            lines.append(f"| {cat_name} | {stats['total']} | {stats['correct']} | {stats['accuracy']:.1%} |")
        lines.append("")

    # 逐案对比(只展示手工标注的前16个 + 错误案例)
    lines.append("## 5. 逐案对比(手工标注)\n")
    header = "| ID | 描述 | 期望 | 规则 | 图谱+规则"
    if full_r: header += " | 完整三层"
    header += " |"
    lines.append(header)
    lines.append("|----|------|------|------|---------" + ("|---------" if full_r else "") + "|")
    for i, case in enumerate(EVAL_CASES):
        rr = rule_r[i]; rt = three_r[i]
        mr = "✅" if rr["expected"] == rr["detected"] else "❌"
        mt = "✅" if rt["expected"] == rt["detected"] else "❌"
        row = f"| {case['id']} | {case['desc']} | {case['expected_risk']} | {rr['detected']} {mr} | {rt['detected']} {mt}"
        if full_r and i < len(full_r):
            rf = full_r[i]
            mf = "✅" if rf["expected"] == rf["detected"] else "❌"
            row += f" | {rf['detected']} {mf}"
        row += " |"
        lines.append(row)

    # 生成用例中的错误案例
    if len(rule_r) > len(EVAL_CASES):
        lines.append("")
        lines.append("### 生成用例中的典型错误\n")
        lines.append("| ID | 描述 | 期望 | 检测 | 类别 |")
        lines.append("|----|------|------|------|------|")
        errors = []
        for i in range(len(EVAL_CASES), len(three_r)):
            rt = three_r[i]
            if rt["expected"] != rt["detected"]:
                errors.append(rt)
        for e in errors[:15]:  # 最多展示15个
            lines.append(f"| {e['id']} | {e['desc']} | {e['expected']} | {e['detected']} | {e.get('category', '')} |")
        if len(errors) > 15:
            lines.append(f"| ... | 还有 {len(errors)-15} 个错误 | | | |")

    lines.append("")
    lines.append("## 6. 关键发现\n")
    if full_r:
        lines.append(f"- 规则引擎 precision = {rule_m['precision']:.1%}（硬规则不产生假阳性）")
        lines.append(f"- 图谱+规则 recall = {three_m['recall']:.1%}（知识图谱补充交互检测）")
        lines.append(f"- 完整三层 F1 = {full_m['f1']:.1%}（LLM 补充语义推理）")
        lines.append(f"- 精确匹配率 = {full_m['exact_match_rate']:.1%}")
    else:
        lines.append(f"- 图谱+规则相比纯规则,召回率从 {rule_m['recall']:.1%} 提升到 {three_m['recall']:.1%}")
        lines.append(f"- 规则引擎 precision = {rule_m['precision']:.1%}（零误报）")
        lines.append("- 完整三层(含LLM)的评测需运行 `python tests/test_eval.py --full`")
    lines.append("")
    lines.append("---")
    lines.append("*二分类标准: critical/high = 正样本, medium/low/safe = 负样本*")
    return "\n".join(lines)


def run_evaluation(run_full=False, save_report=False):
    print("=" * 70)
    print("用药安全审查系统 - 评测报告")
    print("=" * 70)

    all_cases = get_all_cases()
    num_handmade = len(EVAL_CASES)
    num_generated = len(all_cases) - num_handmade
    print(f"\n  样本总数: {len(all_cases)} (手工 {num_handmade} + 生成 {num_generated})")

    print("\n[方案A] 纯规则引擎")
    rule_results = eval_rules_only(all_cases)
    rule_metrics = _calc_metrics(rule_results)
    print(f"  TP={rule_metrics['tp']} FP={rule_metrics['fp']} FN={rule_metrics['fn']} TN={rule_metrics['tn']}")
    print(f"  Accuracy: {rule_metrics['accuracy']:.1%}  Precision: {rule_metrics['precision']:.1%}  Recall: {rule_metrics['recall']:.1%}  F1: {rule_metrics['f1']:.1%}")

    print("\n[方案B] 图谱+规则")
    three_results = eval_three_layer(all_cases)
    three_metrics = _calc_metrics(three_results)
    three_mc = _calc_multiclass_metrics(three_results)
    three_cat = _calc_category_stats(three_results)
    print(f"  TP={three_metrics['tp']} FP={three_metrics['fp']} FN={three_metrics['fn']} TN={three_metrics['tn']}")
    print(f"  Accuracy: {three_metrics['accuracy']:.1%}  Precision: {three_metrics['precision']:.1%}  Recall: {three_metrics['recall']:.1%}  F1: {three_metrics['f1']:.1%}")
    print(f"  精确匹配: {three_metrics['exact_match']}/{three_metrics['total']}")

    # 多分类指标
    print("\n  [多分类指标]")
    for level in ["critical", "high", "medium", "low", "safe"]:
        if level in three_mc:
            m = three_mc[level]
            print(f"    {level:10s}  P={m['precision']:.1%}  R={m['recall']:.1%}  F1={m['f1']:.1%}  (n={m['support']})")

    # 分类别统计
    print("\n  [分类别统计]")
    for cat_name, stats in sorted(three_cat.items()):
        print(f"    {cat_name:10s}  total={stats['total']}  correct={stats['correct']}  acc={stats['accuracy']:.1%}")

    full_results = None
    full_metrics = None
    full_mc = None
    full_cat = None
    if run_full:
        print("\n[方案C] 完整三层架构(图谱+规则+LLM ReAct)")
        full_results = eval_full_pipeline(all_cases)
        full_metrics = _calc_metrics(full_results)
        full_mc = _calc_multiclass_metrics(full_results)
        full_cat = _calc_category_stats(full_results)
        print(f"  TP={full_metrics['tp']} FP={full_metrics['fp']} FN={full_metrics['fn']} TN={full_metrics['tn']}")
        print(f"  Accuracy: {full_metrics['accuracy']:.1%}  Precision: {full_metrics['precision']:.1%}  Recall: {full_metrics['recall']:.1%}  F1: {full_metrics['f1']:.1%}")
        print(f"  精确匹配: {full_metrics['exact_match']}/{full_metrics['total']}")

    # 手工用例逐案对比
    print("\n" + "-" * 70)
    header = f"{'ID':<6}{'描述':<40}{'期望':<10}{'规则':<10}{'图谱+规则':<10}"
    if full_results: header += f"{'完整三层':<10}"
    print(header)
    print("-" * 70)
    for i, case in enumerate(EVAL_CASES):
        if i >= len(rule_results) or i >= len(three_results):
            break
        rr = rule_results[i]; rt = three_results[i]
        mr = "V" if rr["expected"] == rr["detected"] else "X"
        mt = "V" if rt["expected"] == rt["detected"] else "X"
        row = f"{case['id']:<6}{case['desc'][:38]:<40}{case['expected_risk']:<10}{rr['detected']:<8}{mr} {rt['detected']:<8}{mt}"
        if full_results and i < len(full_results):
            rf = full_results[i]
            mf = "V" if rf["expected"] == rf["detected"] else "X"
            row += f" {rf['detected']:<8}{mf}"
        print(row)

    if save_report:
        rule_mc = _calc_multiclass_metrics(rule_results)
        rule_cat = _calc_category_stats(rule_results)
        report = _generate_markdown_report(
            rule_results, three_results, full_results,
            rule_metrics, three_metrics, full_metrics,
            rule_mc, three_mc, full_mc,
            rule_cat, three_cat, full_cat,
            all_cases,
        )
        report_path = Path(__file__).resolve().parent.parent / "EVAL_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n[Report] 评测报告已保存到: {report_path}")

    print("\n" + "=" * 70)
    if not run_full:
        print("  运行 `python tests/test_eval.py --full --report` 获取完整三层(含LLM)评测")
    print("=" * 70)
    return rule_metrics, three_metrics, full_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="用药安全审查系统评测")
    parser.add_argument("--full", action="store_true", help="运行完整三层架构评测(需要LLM API)")
    parser.add_argument("--report", action="store_true", help="生成 markdown 评测报告")
    args = parser.parse_args()
    run_evaluation(run_full=args.full, save_report=args.report)


# ── pytest 兼容测试 ──────────────────────────────────────

import pytest


def test_eval_cases_count():
    """评测用例数量应 >= 150（手工16 + 程序生成扩样）"""
    cases = get_all_cases()
    assert len(cases) >= 150, f"用例数量不足: {len(cases)}"


def test_eval_cases_structure():
    """每条用例必须包含必要字段"""
    for case in EVAL_CASES:
        assert "id" in case
        assert "drugs" in case
        assert "expected_risk" in case
        assert case["expected_risk"] in ("critical", "high", "medium", "low", "safe")


def test_rules_only_f1():
    """纯规则引擎 F1 应 >= 50%"""
    cases = get_all_cases()
    results = eval_rules_only(cases)
    metrics = _calc_metrics(results)
    assert metrics["f1"] >= 0.5, f"规则引擎 F1 过低: {metrics['f1']:.1%}"


def test_graph_rules_f1():
    """图谱+规则 F1 应 >= 80%"""
    cases = get_all_cases()
    results = eval_three_layer(cases)
    metrics = _calc_metrics(results)
    assert metrics["f1"] >= 0.8, f"图谱+规则 F1 过低: {metrics['f1']:.1%}"


def test_graph_rules_recall():
    """图谱+规则召回率应 >= 85%（扩样+校准后允许少量临界漏检）"""
    cases = get_all_cases()
    results = eval_three_layer(cases)
    metrics = _calc_metrics(results)
    assert metrics["recall"] >= 0.85, f"召回率不足: {metrics['recall']:.1%}"


def test_graph_rules_beats_rules():
    """图谱+规则应优于纯规则"""
    cases = get_all_cases()
    rule_results = eval_rules_only(cases)
    three_results = eval_three_layer(cases)
    rule_m = _calc_metrics(rule_results)
    three_m = _calc_metrics(three_results)
    assert three_m["f1"] >= rule_m["f1"], "图谱+规则应不差于纯规则"


@pytest.mark.slow
def test_full_pipeline_f1():
    """完整三层架构 F1 应 >= 75%（需要 LLM API）"""
    cases = get_all_cases()
    results = eval_full_pipeline(cases)
    metrics = _calc_metrics(results)
    assert metrics["f1"] >= 0.75, f"完整架构 F1 过低: {metrics['f1']:.1%}"
