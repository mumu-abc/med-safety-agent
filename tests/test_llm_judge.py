"""LLM-as-Judge 评测:用 LLM 判断系统审查结果是否临床合理。

运行方式:
  python tests/test_llm_judge.py              # 评测全部用例
  python tests/test_llm_judge.py --limit 20   # 只评测前20个
  python tests/test_llm_judge.py --report     # 生成报告

原理:
  1. 对每个用例,运行"图谱+规则"方案(不用LLM,避免循环)
  2. 将审查结果 + 期望结果交给 LLM 做临床合理性判断
  3. LLM 输出: correct / partial / incorrect + 理由
  4. 汇总 LLM-Judge 准确率

面试要点:
  - "我们用 LLM-as-Judge 做自动化评测,减少人工标注依赖"
  - "评测方案本身不依赖被评测的 LLM,避免循环论证"
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.drug_data import build_graph_from_data
from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
from app.rules.safety_rules import run_all_rules
from app.llm import get_llm


JUDGE_PROMPT = """你是一位临床药学专家,负责评判用药安全审查系统的输出质量。

## 处方信息
{prescription_text}

## 系统审查结果
- 检测到的风险等级: {detected_risk}
- 药物交互数: {interaction_count}
- 规则触发数: {rule_count}
- 检测到的交互详情: {interaction_details}
- 规则触发详情: {rule_details}

## 期望结果
- 期望风险等级: {expected_risk}
- 期望最少交互数: {expected_min_interactions}
- 期望最少规则数: {expected_min_rules}

## 评判标准
1. 如果系统检测到的风险 >= 期望风险(如期望high,系统检测critical),视为"正确"
2. 如果系统检测到的风险略低于期望(如期望critical,系统检测high),视为"部分正确"
3. 如果系统将高风险处方判定为安全,或安全处方判定为高风险,视为"错误"
4. 考虑临床实际:某些药物组合虽然有理论风险,但临床常用且可控,可酌情放宽

请输出JSON格式:
{{
  "judgment": "correct" | "partial" | "incorrect",
  "clinical_reasoning": "你的临床判断理由(50字以内)",
  "risk_assessment_agree": true/false
}}"""


def _get_interaction_details(interactions: list[dict]) -> str:
    if not interactions:
        return "无"
    return "; ".join(f"{i['drug_a']}+{i['drug_b']}({i['severity']}:{i['mechanism']})" for i in interactions[:5])


def _get_rule_details(rule_risks: list[dict]) -> str:
    if not rule_risks:
        return "无"
    return "; ".join(f"{r['drug']}({r['severity']}:{r['risk']})" for r in rule_risks[:5])


def eval_case_with_judge(case: dict, graph_result: dict, llm) -> dict:
    """用 LLM 评判单个用例。"""
    prompt = JUDGE_PROMPT.format(
        prescription_text=case.get("prescription_text", case["desc"]),
        detected_risk=graph_result["detected"],
        interaction_count=graph_result.get("interactions", 0),
        rule_count=graph_result.get("rules", 0),
        interaction_details=graph_result.get("interaction_details", "无"),
        rule_details=graph_result.get("rule_details", "无"),
        expected_risk=case["expected_risk"],
        expected_min_interactions=case.get("expected_min_interactions", 0),
        expected_min_rules=case.get("expected_min_rules", 0),
    )

    try:
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        # 提取 JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        result = json.loads(content)
        return {
            "judgment": result.get("judgment", "unknown"),
            "reasoning": result.get("clinical_reasoning", ""),
            "risk_agree": result.get("risk_assessment_agree", False),
        }
    except Exception as e:
        return {
            "judgment": "error",
            "reasoning": str(e)[:100],
            "risk_agree": False,
        }


def run_llm_judge_eval(cases: list[dict], limit: int = 0) -> dict:
    """运行 LLM-as-Judge 评测。"""
    build_graph_from_data()
    llm = get_llm()

    if limit > 0:
        cases = cases[:limit]

    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] {case['id']}: {case['desc'][:40]}...", end="", flush=True)

        # 运行图谱+规则方案
        ids = [get_drug_by_name(n)["id"] for n in case["drugs"] if get_drug_by_name(n)]
        interactions = find_interactions(ids) if len(ids) >= 2 else []
        contras = []
        for name in case["drugs"]:
            d = get_drug_by_name(name)
            if d and case.get("patient", {}).get("conditions"):
                contras.extend(find_contraindications(d["id"], case["patient"]["conditions"]))
        drugs_info = [{"id": did, "name": n} for did, n in zip(ids, case["drugs"])]
        rule_risks = run_all_rules(drugs_info, case.get("patient", {}))

        from tests.test_eval import _risk_level_num
        all_sev = [_risk_level_num(i["severity"]) for i in interactions]
        all_sev += [4 for _ in contras]
        all_sev += [_risk_level_num(r["severity"]) for r in rule_risks]
        if all_sev:
            max_sev = max(all_sev)
            detected = {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(max_sev, "low")
        else:
            detected = "safe"

        graph_result = {
            "detected": detected,
            "interactions": len(interactions),
            "rules": len(rule_risks),
            "interaction_details": _get_interaction_details(interactions),
            "rule_details": _get_rule_details(rule_risks),
        }

        # LLM 判断
        judge_result = eval_case_with_judge(case, graph_result, llm)
        print(f" -> {judge_result['judgment']}")

        results.append({
            "id": case["id"],
            "desc": case["desc"],
            "expected": case["expected_risk"],
            "detected": detected,
            "judgment": judge_result["judgment"],
            "reasoning": judge_result["reasoning"],
            "risk_agree": judge_result["risk_agree"],
            "category": case.get("category", ""),
        })

    return _aggregate_judge_results(results)


def _aggregate_judge_results(results: list[dict]) -> dict:
    """汇总 LLM-Judge 结果。"""
    total = len(results)
    correct = sum(1 for r in results if r["judgment"] == "correct")
    partial = sum(1 for r in results if r["judgment"] == "partial")
    incorrect = sum(1 for r in results if r["judgment"] == "incorrect")
    errors = sum(1 for r in results if r["judgment"] == "error")

    # 按类别统计
    category_stats = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0, "partial": 0, "incorrect": 0}
        category_stats[cat]["total"] += 1
        if r["judgment"] in category_stats[cat]:
            category_stats[cat][r["judgment"]] += 1

    return {
        "total": total,
        "correct": correct,
        "partial": partial,
        "incorrect": incorrect,
        "errors": errors,
        "accuracy": round(correct / total, 3) if total else 0,
        "partial_accuracy": round((correct + partial) / total, 3) if total else 0,
        "category_stats": category_stats,
        "details": results,
    }


def generate_judge_report(judge_result: dict) -> str:
    """生成 LLM-Judge 评测报告。"""
    lines = []
    lines.append("# LLM-as-Judge 评测报告\n")
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"> 评测样本数: {judge_result['total']}\n")

    lines.append("## 总览\n")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 总样本数 | {judge_result['total']} |")
    lines.append(f"| 正确(correct) | {judge_result['correct']} |")
    lines.append(f"| 部分正确(partial) | {judge_result['partial']} |")
    lines.append(f"| 错误(incorrect) | {judge_result['incorrect']} |")
    lines.append(f"| LLM调用异常 | {judge_result['errors']} |")
    lines.append(f"| **准确率(correct)** | **{judge_result['accuracy']:.1%}** |")
    lines.append(f"| 宽松准确率(correct+partial) | {judge_result['partial_accuracy']:.1%} |")
    lines.append("")

    # 分类别
    lines.append("## 分类别统计\n")
    lines.append("| 类别 | 总数 | 正确 | 部分正确 | 错误 |")
    lines.append("|------|------|------|----------|------|")
    for cat, stats in sorted(judge_result["category_stats"].items()):
        lines.append(f"| {cat} | {stats['total']} | {stats['correct']} | {stats['partial']} | {stats['incorrect']} |")
    lines.append("")

    # 错误案例详情
    errors = [r for r in judge_result["details"] if r["judgment"] in ("incorrect", "error")]
    if errors:
        lines.append("## 错误案例\n")
        lines.append("| ID | 描述 | 期望 | 检测 | 判定 | 理由 |")
        lines.append("|----|------|------|------|------|------|")
        for e in errors[:20]:
            lines.append(f"| {e['id']} | {e['desc'][:30]} | {e['expected']} | {e['detected']} | {e['judgment']} | {e['reasoning'][:40]} |")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-as-Judge 评测")
    parser.add_argument("--limit", type=int, default=0, help="限制评测用例数(0=全部)")
    parser.add_argument("--report", action="store_true", help="生成 markdown 报告")
    args = parser.parse_args()

    from tests.test_eval import get_all_cases
    all_cases = get_all_cases()

    print(f"LLM-as-Judge 评测: {len(all_cases)} 个用例")
    print("=" * 60)

    judge_result = run_llm_judge_eval(all_cases, limit=args.limit)

    print("\n" + "=" * 60)
    print(f"准确率(correct): {judge_result['accuracy']:.1%}")
    print(f"宽松准确率(correct+partial): {judge_result['partial_accuracy']:.1%}")
    print(f"  correct={judge_result['correct']}  partial={judge_result['partial']}  incorrect={judge_result['incorrect']}")

    if args.report:
        report = generate_judge_report(judge_result)
        report_path = Path(__file__).resolve().parent.parent / "JUDGE_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n[Report] LLM-Judge 报告已保存到: {report_path}")

    # 保存详细结果
    detail_path = Path(__file__).resolve().parent.parent / "data" / "judge_results.json"
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(judge_result["details"], f, ensure_ascii=False, indent=2)
    print(f"[Detail] 详细结果已保存到: {detail_path}")


# ── pytest 兼容测试 ──────────────────────────────────────

import pytest


@pytest.mark.slow
def test_llm_judge_accuracy():
    """LLM-as-Judge 准确率应 >= 70%（需要 LLM API）"""
    from tests.test_eval import get_all_cases
    all_cases = get_all_cases()
    judge_result = run_llm_judge_eval(all_cases, limit=20)
    assert judge_result["accuracy"] >= 0.7, f"Judge 准确率过低: {judge_result['accuracy']:.1%}"
