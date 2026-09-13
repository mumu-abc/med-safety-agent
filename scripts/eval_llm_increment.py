"""LLM 增量价值评测:证明 Agent/LLM 在规则+图谱之外带来的可量化收益。

设计原则(面试可讲):
  Track A  Graph+Rules@Oracle  — 用标注的 ground-truth 药名跑确定性基线(无 LLM)
  Track B  Graph+Rules@LLMParse — 只用 LLM 解析药名,后续仍走图谱+规则(隔离解析增量)
  Track C  Parse + Semantic LLM + Rules Floor — 隔离推理增量(不跑慢速 ReAct)

运行:
  python -u scripts/eval_llm_increment.py --oracle
  python -u scripts/eval_llm_increment.py --report --skip-parse-track
  python -u scripts/eval_llm_increment.py --report --skip-parse-track --limit 6
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_PATH = ROOT / "data" / "eval_llm_increment.json"
REPORT_PATH = ROOT / "LLM_INCREMENT_REPORT.md"
RESULTS_PATH = ROOT / "data" / "llm_increment_results.json"

RISK_ORDER = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def load_cases() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _level_num(level: str) -> int:
    return RISK_ORDER.get(level, -1)


def _max_severity(*groups: list) -> str:
    best = "safe"
    for items in groups:
        for item in items or []:
            sev = item.get("severity", "safe")
            if _level_num(sev) > _level_num(best):
                best = sev
    return best


def _patient_from_text(text: str) -> dict:
    import re
    patient = {
        "age": None, "gender": "", "conditions": [], "allergies": [],
        "liver_function": "normal", "renal_function": "normal", "pregnancy": "no",
    }
    if "eGFR" in text or "肾功能" in text:
        if any(x in text for x in ("28", "下降", "受损", "不全")):
            patient["renal_function"] = "impaired"
    if "溃疡" in text or "出血史" in text:
        patient["conditions"] = ["消化道溃疡"]
    if "哮喘" in text:
        patient["conditions"] = ["哮喘"]
    if "孕妇" in text or "孕" in text:
        patient["pregnancy"] = "yes"
    m = re.search(r"(\d{2,3})\s*岁", text)
    if m:
        patient["age"] = int(m.group(1))
    return patient


def eval_oracle(cases: list[dict]) -> list[dict]:
    """Track A: 用标注药名跑图谱+规则,不调用 LLM。"""
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    from app.rules.safety_rules import run_all_rules

    build_graph_from_data()
    results = []
    for case in cases:
        drugs = case["expected_drugs"]
        ids, drugs_info = [], []
        for name in drugs:
            d = get_drug_by_name(name)
            if d:
                ids.append(d["id"])
                drugs_info.append({"id": d["id"], "name": d.get("name", name)})
            else:
                drugs_info.append({"id": name, "name": name})

        patient = _patient_from_text(case["prescription_text"])
        interactions = find_interactions(ids) if len(ids) >= 2 else []
        contras = []
        for did in ids:
            contras.extend(find_contraindications(did, patient.get("conditions") or []))
        rule_risks = run_all_rules(drugs_info, patient)
        detected = _max_severity(interactions, contras, rule_risks)
        results.append({
            "id": case["id"], "track": case["track"], "category": case["category"],
            "desc": case["desc"], "expected": case["expected_risk"], "detected": detected,
            "exact": detected == case["expected_risk"],
            "binary_ok": (detected in ("critical", "high")) == (case["expected_risk"] in ("critical", "high")),
            "why_llm": case.get("why_llm", ""), "source": "oracle",
            "parsed_drugs": drugs, "n_interactions": len(interactions), "n_rules": len(rule_risks),
        })
    return results


def _cached_parse(case: dict, cache: dict):
    from app.agents.prescription_agent import parse_prescription
    key = case["id"]
    if key in cache:
        return cache[key]
    print(f"  parse {key} ...", flush=True)
    rx = parse_prescription(case["prescription_text"])
    cache[key] = rx
    return rx


def eval_parse_then_rules(cases: list[dict], parse_cache: dict | None = None) -> list[dict]:
    """Track B: LLM 解析处方 → 图谱+规则。"""
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    from app.rules.safety_rules import run_all_rules

    build_graph_from_data()
    cache = parse_cache if parse_cache is not None else {}
    results = []
    for case in cases:
        try:
            rx = _cached_parse(case, cache)
            drug_names = [d.name for d in rx.drugs if d.name]
            ids, drugs_info = [], []
            for name in drug_names:
                d = get_drug_by_name(name)
                if d:
                    ids.append(d["id"])
                    drugs_info.append({"id": d["id"], "name": d.get("name", name)})
                else:
                    drugs_info.append({"id": name, "name": name})
            patient = {
                "age": rx.patient.age, "gender": rx.patient.gender or "",
                "conditions": rx.patient.conditions or [], "allergies": rx.patient.allergies or [],
                "liver_function": rx.patient.liver_function or "normal",
                "renal_function": rx.patient.renal_function or "normal",
                "pregnancy": rx.patient.pregnancy or "no",
            }
            interactions = find_interactions(ids) if len(ids) >= 2 else []
            contras = []
            for did in ids:
                contras.extend(find_contraindications(did, patient.get("conditions") or []))
            rule_risks = run_all_rules(drugs_info, patient)
            detected = _max_severity(interactions, contras, rule_risks)
            results.append({
                "id": case["id"], "track": case["track"], "category": case["category"],
                "desc": case["desc"], "expected": case["expected_risk"], "detected": detected,
                "exact": detected == case["expected_risk"],
                "binary_ok": (detected in ("critical", "high")) == (case["expected_risk"] in ("critical", "high")),
                "why_llm": case.get("why_llm", ""), "source": "parse+rules",
                "parsed_drugs": drug_names,
                "n_interactions": len(interactions), "n_rules": len(rule_risks),
            })
        except Exception as e:
            results.append({
                "id": case["id"], "track": case["track"], "category": case["category"],
                "desc": case["desc"], "expected": case["expected_risk"],
                "detected": "error", "exact": False, "binary_ok": False,
                "why_llm": case.get("why_llm", ""), "source": "parse_error",
                "parsed_drugs": [], "error": str(e),
            })
    return results


def eval_full(cases: list[dict], parse_cache: dict | None = None) -> list[dict]:
    """Track C: 解析 + 单次语义评估 + 规则兜底(不跑慢速 ReAct)。"""
    from app.agents.semantic_assess import assess_risk_llm_once, build_context_text, merge_rule_floor
    from app.graph.drug_data import build_graph_from_data
    from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
    from app.rules.safety_rules import run_all_rules

    build_graph_from_data()
    cache = parse_cache if parse_cache is not None else {}
    results = []
    for i, case in enumerate(cases, 1):
        print(f"  full {i}/{len(cases)} {case['id']} ...", flush=True)
        try:
            rx = _cached_parse(case, cache)
            drug_names = [d.name for d in rx.drugs if d.name]
            ids, drugs_info = [], []
            for name in drug_names:
                d = get_drug_by_name(name)
                if d:
                    ids.append(d["id"])
                    drugs_info.append({"id": d["id"], "name": d.get("name", name)})
                else:
                    drugs_info.append({"id": name, "name": name})
            patient = {
                "age": rx.patient.age, "gender": rx.patient.gender or "",
                "conditions": rx.patient.conditions or [], "allergies": rx.patient.allergies or [],
                "liver_function": rx.patient.liver_function or "normal",
                "renal_function": rx.patient.renal_function or "normal",
                "pregnancy": rx.patient.pregnancy or "no",
            }
            interactions = find_interactions(ids) if len(ids) >= 2 else []
            contras = []
            for did in ids:
                contras.extend(find_contraindications(did, patient.get("conditions") or []))
            rule_risks = run_all_rules(drugs_info, patient)

            print(f"  assess {case['id']} ...", flush=True)
            ctx = build_context_text(case["prescription_text"], drugs_info, patient, rule_risks, interactions)
            llm_assess = assess_risk_llm_once(ctx)
            detected, merged = merge_rule_floor(llm_assess.overall_risk, llm_assess.risks, rule_risks)
            llm_only = [r for r in merged if getattr(r, "source", "") == "llm"]
            print(f"  -> {case['id']} expected={case['expected_risk']} got={detected}", flush=True)
        except Exception as e:
            detected = "error"
            llm_only = []
            drug_names = []
            print(f"  warn {case['id']}: {e}", flush=True)

        results.append({
            "id": case["id"], "track": case["track"], "category": case["category"],
            "desc": case["desc"], "expected": case["expected_risk"], "detected": detected,
            "exact": detected == case["expected_risk"],
            "binary_ok": (detected in ("critical", "high")) == (case["expected_risk"] in ("critical", "high")),
            "why_llm": case.get("why_llm", ""), "source": "full",
            "parsed_drugs": drug_names, "n_llm_risks": len(llm_only),
            "llm_risk_summaries": [getattr(r, "description", "")[:80] for r in llm_only[:3]],
        })
    return results


def summarize(name: str, results: list[dict]) -> dict:
    n = len(results) or 1
    exact = sum(1 for r in results if r.get("exact"))
    binary = sum(1 for r in results if r.get("binary_ok"))
    by_track: dict[str, list[dict]] = {}
    for r in results:
        by_track.setdefault(r.get("track", "?"), []).append(r)
    track_stats = {}
    for t, rs in by_track.items():
        track_stats[t] = {
            "n": len(rs),
            "exact": sum(1 for r in rs if r.get("exact")),
            "exact_rate": round(sum(1 for r in rs if r.get("exact")) / len(rs), 3) if rs else 0,
            "binary_rate": round(sum(1 for r in rs if r.get("binary_ok")) / len(rs), 3) if rs else 0,
        }
    return {
        "name": name, "n": len(results), "exact": exact, "exact_rate": round(exact / n, 3),
        "binary": binary, "binary_rate": round(binary / n, 3), "by_track": track_stats,
    }


def generate_report(all_tracks: dict[str, list[dict]], summaries: dict[str, dict]) -> str:
    lines = []
    lines.append("# LLM 增量价值评测报告")
    lines.append("")
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 难例数: {len(all_tracks.get('oracle', []))}  (parse / reason / negative)")
    lines.append("")
    lines.append("## 1. 为什么需要这份报告")
    lines.append("")
    lines.append("主评测集(77条)中 61 条由图谱程序生成,图谱+规则与「含 LLM」方案 F1 几乎相同,")
    lines.append("**无法证明 LLM/Agent 的增量价值**。本报告用「规则/图谱设计时未覆盖」的难例,")
    lines.append("拆开测量解析增量与推理增量。")
    lines.append("")
    lines.append("## 2. 三轨对比总览")
    lines.append("")
    lines.append("| 轨道 | 说明 | 精确匹配 | 精确率 | 二分类正确率 |")
    lines.append("|------|------|----------|--------|--------------|")
    labels = {
        "oracle": "A. Graph+Rules @ 标注药名(无 LLM)",
        "parse": "B. LLM 解析 → Graph+Rules",
        "full": "C. 解析 + 语义评估 + 规则兜底",
    }
    for key in ("oracle", "parse", "full"):
        if key not in summaries:
            continue
        s = summaries[key]
        lines.append(
            f"| {labels[key]} | {s['n']} 条 | {s['exact']}/{s['n']} | {s['exact_rate']:.1%} | {s['binary_rate']:.1%} |"
        )
    lines.append("")

    if "oracle" in all_tracks and "full" in all_tracks:
        lines.append("## 3. 逐案:Oracle 基线 vs Full")
        lines.append("")
        lines.append("| ID | Track | 期望 | A.Oracle | C.Full | A对 | C对 | LLM 增量说明 |")
        lines.append("|----|-------|------|----------|--------|-----|-----|--------------|")
        full_map = {r["id"]: r for r in all_tracks["full"]}
        for o in all_tracks["oracle"]:
            f = full_map.get(o["id"], {})
            lines.append(
                f"| {o['id']} | {o['track']} | {o['expected']} | {o['detected']} | {f.get('detected', '?')} | "
                f"{'Y' if o['exact'] else 'N'} | {'Y' if f.get('exact') else 'N'} | {o.get('why_llm', '')[:48]} |"
            )
        lines.append("")
        gained, lost = [], []
        for o in all_tracks["oracle"]:
            f = full_map.get(o["id"], {})
            if not f:
                continue
            if f.get("exact") and not o.get("exact"):
                gained.append(o["id"])
            elif o.get("exact") and not f.get("exact"):
                lost.append(o["id"])
        lines.append("## 4. LLM 净增量")
        lines.append("")
        lines.append(f"- Full 修好 Oracle 错判: **{len(gained)}** 条 `{gained}`")
        lines.append(f"- Full 弄坏 Oracle 对判: **{len(lost)}** 条 `{lost}`")
        lines.append(f"- 净增量: **{len(gained) - len(lost):+d}** 条精确匹配")
        lines.append("")

    lines.append("## 5. 结论(面试可用)")
    lines.append("")
    o = summaries.get("oracle")
    f = summaries.get("full")
    if o and f:
        delta = f["exact_rate"] - o["exact_rate"]
        lines.append(
            f"在 {o['n']} 条「规则/图谱覆盖不到」的难例上:确定性基线精确率 **{o['exact_rate']:.1%}**,"
            f"加入 LLM 解析与语义评估后 **{f['exact_rate']:.1%}**,提升 **{delta:+.1%}**。"
        )
        lines.append("")
        lines.append("这回答了「为什么不能只写规则引擎」:")
        lines.append("1. 自由文本/商品名解析 —— LLM 负责把病历变成结构化药名")
        lines.append("2. 剂量、病史、图谱外药理知识 —— LLM 负责语义推理")
        lines.append("3. 已知相互作用与硬禁忌 —— 图谱+规则仍是底线,且 overall_risk 不得被 LLM 降级")
    lines.append("")
    lines.append("---")
    lines.append("*难例集不替代主评测集;主评测衡量已覆盖分布上的回归,本集衡量分布外增量。*")
    lines.append("*Track C 使用单次 structured output 而非 ReAct 工具循环:在部分国产模型上 ReAct 延迟过高,")
    lines.append("受控对比需要稳定可复现的推理入口;生产路径仍保留 ReAct + 图谱工具。*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="LLM 增量价值评测")
    parser.add_argument("--oracle", action="store_true", help="只跑 Track A(无 LLM)")
    parser.add_argument("--skip-full", action="store_true", help="跳过 Track C")
    parser.add_argument("--skip-parse-track", action="store_true", help="跳过 Track B")
    parser.add_argument("--report", action="store_true", help="写入 markdown 报告")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 条")
    args = parser.parse_args()

    cases = load_cases()
    if args.limit and args.limit > 0:
        cases = cases[: args.limit]
    print(f"LLM 增量难例: {len(cases)} 条", flush=True)
    tracks: dict[str, list[dict]] = {}
    summaries: dict[str, dict] = {}
    parse_cache: dict = {}

    print("\n[Track A] Graph+Rules @ 标注药名 (无 LLM)", flush=True)
    tracks["oracle"] = eval_oracle(cases)
    summaries["oracle"] = summarize("A.Oracle", tracks["oracle"])
    s = summaries["oracle"]
    print(f"  exact={s['exact']}/{s['n']} ({s['exact_rate']:.1%})  binary={s['binary_rate']:.1%}", flush=True)
    RESULTS_PATH.write_text(json.dumps({"summaries": summaries, "results": tracks}, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.oracle:
        if not args.skip_parse_track:
            print("\n[Track B] LLM 解析 → Graph+Rules", flush=True)
            tracks["parse"] = eval_parse_then_rules(cases, parse_cache)
            summaries["parse"] = summarize("B.Parse+Rules", tracks["parse"])
            s = summaries["parse"]
            print(f"  exact={s['exact']}/{s['n']} ({s['exact_rate']:.1%})  binary={s['binary_rate']:.1%}", flush=True)
            RESULTS_PATH.write_text(json.dumps({"summaries": summaries, "results": tracks}, ensure_ascii=False, indent=2), encoding="utf-8")

        if not args.skip_full:
            print("\n[Track C] 解析 + 语义评估 + 规则兜底", flush=True)
            tracks["full"] = eval_full(cases, parse_cache)
            summaries["full"] = summarize("C.Full", tracks["full"])
            s = summaries["full"]
            print(f"  exact={s['exact']}/{s['n']} ({s['exact_rate']:.1%})  binary={s['binary_rate']:.1%}", flush=True)

    print("\n" + "=" * 70, flush=True)
    for key, s in summaries.items():
        print(f"  {s['name']}: exact={s['exact_rate']:.1%} binary={s['binary_rate']:.1%}", flush=True)
    print("=" * 70, flush=True)

    if args.report and tracks:
        report = generate_report(tracks, summaries)
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"\n[Report] {REPORT_PATH}", flush=True)

    RESULTS_PATH.write_text(json.dumps({"summaries": summaries, "results": tracks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Data] {RESULTS_PATH}", flush=True)


if __name__ == "__main__":
    main()
