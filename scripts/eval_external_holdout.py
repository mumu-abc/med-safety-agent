"""外部临床知识 holdout 评测：检验图谱+规则在非自产样本上的真实表现。

数据: data/eval_external_holdout.json
  按公开药品说明书/临床指南常识手工标注,不从本项目 drug_data 生成。

运行:
  python -u scripts/eval_external_holdout.py
  python -u scripts/eval_external_holdout.py --report
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_PATH = ROOT / "data" / "eval_external_holdout.json"
REPORT_PATH = ROOT / "EXTERNAL_HOLDOUT_REPORT.md"

RISK_ORDER = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def load_cases() -> list[dict]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def _max_sev(*groups) -> str:
    best = "safe"
    for items in groups:
        for it in items or []:
            sev = it.get("severity", "safe")
            if RISK_ORDER.get(sev, -1) > RISK_ORDER.get(best, 0):
                best = sev
    return best


def eval_graph_rules(cases: list[dict]) -> list[dict]:
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    from app.rules.safety_rules import run_all_rules

    build_graph_from_data()
    results = []
    for case in cases:
        drugs = case["drugs"]
        patient = {
            "age": case["patient"].get("age"),
            "gender": case["patient"].get("gender", ""),
            "conditions": case["patient"].get("conditions") or [],
            "allergies": case["patient"].get("allergies") or [],
            "liver_function": case["patient"].get("liver_function", "normal"),
            "renal_function": case["patient"].get("renal_function", "normal"),
            "pregnancy": case["patient"].get("pregnancy", "no"),
        }
        ids, drugs_info, missing = [], [], []
        for name in drugs:
            d = get_drug_by_name(name)
            if d:
                ids.append(d["id"])
                drugs_info.append({"id": d["id"], "name": d.get("name", name)})
            else:
                missing.append(name)
                drugs_info.append({"id": name, "name": name})

        interactions = find_interactions(ids) if len(ids) >= 2 else []
        contras = []
        for did in ids:
            contras.extend(find_contraindications(did, patient.get("conditions") or []))
        rule_risks = run_all_rules(drugs_info, patient)
        detected = _max_sev(interactions, contras, rule_risks)
        results.append({
            "id": case["id"],
            "drugs": drugs,
            "expected": case["expected_risk"],
            "detected": detected,
            "exact": detected == case["expected_risk"],
            "binary_ok": (detected in ("critical", "high")) == (case["expected_risk"] in ("critical", "high")),
            "in_graph": len(missing) == 0,
            "missing": missing,
            "n_interactions": len(interactions),
            "n_rules": len(rule_risks),
            "n_contras": len(contras),
            "source": case.get("source", ""),
        })
    return results


def metrics(results: list[dict]) -> dict:
    n = len(results) or 1
    tp = fp = fn = tn = 0
    for r in results:
        exp_h = r["expected"] in ("critical", "high")
        det_h = r["detected"] in ("critical", "high")
        if exp_h and det_h:
            tp += 1
        elif not exp_h and det_h:
            fp += 1
        elif exp_h and not det_h:
            fn += 1
        else:
            tn += 1
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    exact = sum(1 for r in results if r["exact"])
    return {
        "n": len(results), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3),
        "exact": exact, "exact_rate": round(exact / n, 3),
        "binary_rate": round(sum(1 for r in results if r["binary_ok"]) / n, 3),
        "in_graph_n": sum(1 for r in results if r["in_graph"]),
        "missing_drug_cases": sum(1 for r in results if not r["in_graph"]),
    }


def write_report(results: list[dict], m: dict) -> str:
    lines = []
    lines.append("# 外部临床知识 Holdout 评测报告")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 样本数: {m['n']}（全部手工标注,非本项目图谱生成）")
    lines.append("")
    lines.append("## 1. 总览（图谱+规则,无 LLM）")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| Accuracy(二分类) | {(m['tp']+m['tn'])/max(m['n'],1):.1%} |")
    lines.append(f"| Precision | {m['precision']:.1%} |")
    lines.append(f"| Recall | {m['recall']:.1%} |")
    lines.append(f"| F1 | {m['f1']:.1%} |")
    lines.append(f"| 精确匹配(多分类) | {m['exact']}/{m['n']} ({m['exact_rate']:.1%}) |")
    lines.append(f"| 二分类正确 | {m['binary_rate']:.1%} |")
    lines.append(f"| 药物均在图谱内 | {m['in_graph_n']}/{m['n']} |")
    lines.append(f"| 含图谱外药名 | {m['missing_drug_cases']} 条 |")
    lines.append("")
    lines.append("## 2. 与主评测集的关系")
    lines.append("")
    lines.append("| 集合 | 来源 | 图谱+规则 F1 | 解读 |")
    lines.append("|------|------|--------------|------|")
    lines.append("| 主集 191 条 | 手工16+程序生成175 | 见 EVAL_REPORT | 分布内回归,**勿单独当卖点** |")
    lines.append(f"| 本 holdout {m['n']} 条 | 外部临床常识手工标注 | **{m['f1']:.1%}** | 更接近真实泛化 |")
    lines.append("")
    lines.append("## 3. 逐案")
    lines.append("")
    lines.append("| ID | 药物 | 期望 | 检测 | 二分 | 在图谱 | 说明 |")
    lines.append("|----|------|------|------|------|--------|------|")
    for r in results:
        mark = "Y" if r["binary_ok"] else "N"
        ig = "Y" if r["in_graph"] else f"N{r['missing']}"
        drugs = "+".join(r["drugs"])
        lines.append(
            f"| {r['id']} | {drugs} | {r['expected']} | {r['detected']} | {mark} | {ig} | {r['source'][:36]} |"
        )
    lines.append("")
    errs = [r for r in results if not r["binary_ok"]]
    lines.append("## 4. 二分类错误分析")
    lines.append("")
    if not errs:
        lines.append("无二分类错误。")
    else:
        lines.append("| ID | 期望 | 检测 | 缺失药 | 规则/交互数 |")
        lines.append("|----|------|------|--------|-------------|")
        for r in errs:
            lines.append(
                f"| {r['id']} | {r['expected']} | {r['detected']} | {r['missing'] or '-'} | "
                f"i={r['n_interactions']} r={r['n_rules']} c={r['n_contras']} |"
            )
    lines.append("")
    lines.append("## 5. 面试话术")
    lines.append("")
    lines.append(
        f"外部 holdout（{m['n']} 条,非自产）上图谱+规则二分类 F1={m['f1']:.1%},"
        f"精确匹配 {m['exact']}/{m['n']}（{m['exact_rate']:.1%}）。"
        "主集大量样本自图谱生成,holdout 全部手工标注——两个数都要报。"
        "剩余误差集中在 severity 边界（high vs critical）。"
    )
    lines.append("")
    lines.append("---")
    lines.append("*本报告为技术评测,不构成临床用药建议。*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    cases = load_cases()
    print(f"外部 holdout: {len(cases)} 条", flush=True)
    results = eval_graph_rules(cases)
    m = metrics(results)

    print(f"  二分类: P={m['precision']:.1%} R={m['recall']:.1%} F1={m['f1']:.1%} acc_binary={m['binary_rate']:.1%}", flush=True)
    print(f"  精确匹配: {m['exact']}/{m['n']} ({m['exact_rate']:.1%})", flush=True)
    print(f"  图谱外药物 case: {m['missing_drug_cases']}", flush=True)

    print("\n逐案(binary fail 标 *):", flush=True)
    for r in results:
        flag = "" if r["binary_ok"] else " *"
        miss = f" missing={r['missing']}" if r["missing"] else ""
        print(f"  {r['id']} exp={r['expected']:8} got={r['detected']:8}{flag}{miss}", flush=True)

    if args.report:
        REPORT_PATH.write_text(write_report(results, m), encoding="utf-8")
        print(f"\n[Report] {REPORT_PATH}", flush=True)

    out = ROOT / "data" / "external_holdout_results.json"
    # 注意: data/*_results.json 在 .gitignore,本地留存即可
    out.write_text(json.dumps({"metrics": m, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Data] {out}", flush=True)


if __name__ == "__main__":
    main()
