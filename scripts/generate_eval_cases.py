"""批量生成评测用例:从药物图谱数据程序化生成标注样本。

运行方式:
  python scripts/generate_eval_cases.py              # 生成 JSON
  python scripts/generate_eval_cases.py --preview    # 预览前10个用例

生成策略(5大类):
  1. 高风险-已知交互: 从 INTERACTIONS 取 critical/high 组合
  2. 特殊人群禁忌: 孕妇/儿童/老年人 + 禁忌药物
  3. 中风险组合: medium 级交互
  4. 安全组合: 无交互药物对
  5. 边界/陷阱用例: 多药联用、规则与图谱交叉
"""
import sys
import json
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.drug_data import DRUGS, INTERACTIONS, ALTERNATIVES

random.seed(42)

# ---- 药物 ID → 名称映射 ----
DRUG_MAP = {d["id"]: d for d in DRUGS}
DRUG_IDS = [d["id"] for d in DRUGS]

# ---- 交互索引 ----
INTERACTION_MAP = {}
for a, b, severity, mechanism in INTERACTIONS:
    key = tuple(sorted([a, b]))
    INTERACTION_MAP[key] = {"severity": severity, "mechanism": mechanism}


def _get_interaction(a: str, b: str) -> dict | None:
    key = tuple(sorted([a, b]))
    return INTERACTION_MAP.get(key)


def _drug_name(drug_id: str) -> str:
    return DRUG_MAP.get(drug_id, {}).get("name", drug_id)


def _make_prescription(drug_ids: list[str], patient: dict) -> str:
    """生成模拟处方文本。"""
    lines = []
    # 患者信息
    age = patient.get("age", 45)
    gender = patient.get("gender", "男")
    conditions = patient.get("conditions", [])
    pregnancy = patient.get("pregnancy", "no")

    gender_str = "男" if gender in ("男", "male") else "女"
    cond_str = "、".join(conditions) if conditions else "体检"
    preg_str = f",孕{random.randint(8, 36)}周" if pregnancy == "yes" else ""

    lines.append(f"患者{gender_str},{age}岁{preg_str},{cond_str}")
    lines.append("处方:")

    for i, did in enumerate(drug_ids, 1):
        d = DRUG_MAP.get(did, {})
        name = d.get("name", did)
        cat = d.get("category", "")
        # 随机剂量
        dose = _random_dose(did)
        lines.append(f"{i}. {name} {dose}")

    return "\n".join(lines)


def _random_dose(drug_id: str) -> str:
    """根据药物类型生成合理剂量。"""
    doses = {
        "warfarin": "2.5mg qd", "aspirin": "100mg qd", "clopidogrel": "75mg qd",
        "ibuprofen": "400mg prn", "acetaminophen": "500mg prn", "metformin": "500mg bid",
        "amlodipine": "5mg qd", "atorvastatin": "20mg qn", "simvastatin": "20mg qn",
        "metoprolol": "47.5mg qd", "losartan": "50mg qd", "valsartan": "80mg qd",
        "lisinopril": "10mg qd", "enalapril": "10mg bid", "omeprazole": "20mg qd",
        "diazepam": "5mg qn", "alprazolam": "0.4mg qn", "morphine": "10mg q12h",
        "fluoxetine": "20mg qd", "sertraline": "50mg qd", "ciprofloxacin": "500mg bid",
        "digoxin": "0.125mg qd", "furosemide": "20mg qd", "spironolactone": "20mg qd",
        "verapamil": "80mg tid", "diltiazem": "30mg tid", "fluconazole": "200mg qd",
        "clarithromycin": "500mg bid", "erythromycin": "500mg qid",
        "carbamazepine": "200mg bid", "valproate": "500mg bid", "lamotrigine": "100mg bid",
        "glibenclamide": "5mg qd", "insulin": "10u ac", "levothyroxine": "50μg qd",
        "lithium": "300mg bid", "cyclosporine": "100mg bid", "tacrolimus": "1mg bid",
        "azathioprine": "50mg qd", "methotrexate": "10mg qw", "colchicine": "0.5mg bid",
        "tramadol": "50mg prn", "oxycodone": "5mg prn", "codeine": "30mg prn",
        "nitroglycerin": "0.5mg prn", "sildenafil": "50mg prn",
        "gentamicin": "80mg q8h", "vancomycin": "1g q12h", "linezolid": "600mg q12h",
        "prednisone": "10mg qd", "dexamethasone": "4mg qd",
    }
    return doses.get(drug_id, "10mg bid")


# ---- 用例生成器 ----

def _case_id(category: str, index: int) -> str:
    return f"{category}{index:03d}"


def _make_patient(age: int = 45, gender: str = "男", conditions: list[str] = None,
                  pregnancy: str = "no", liver: str = "normal", renal: str = "normal") -> dict:
    return {
        "age": age, "gender": gender,
        "conditions": conditions or [],
        "pregnancy": pregnancy,
        "liver_function": liver,
        "renal_function": renal,
    }


def generate_high_risk_interactions(n: int = 18) -> list[dict]:
    """从已知 critical/high 交互中生成用例。"""
    critical_pairs = [(a, b, sev, mech) for a, b, sev, mech in INTERACTIONS if sev == "critical"]
    high_pairs = [(a, b, sev, mech) for a, b, sev, mech in INTERACTIONS if sev == "high"]

    # 优先取 critical，不够用 high 补
    random.shuffle(critical_pairs)
    random.shuffle(high_pairs)
    selected = (critical_pairs + high_pairs)[:n]

    cases = []
    for i, (a, b, severity, mechanism) in enumerate(selected):
        # 随机患者
        age = random.choice([45, 55, 60, 65, 70, 72, 75])
        gender = random.choice(["男", "女"])
        patient = _make_patient(age=age, gender=gender,
                                conditions=random.sample(["高血压", "冠心病", "糖尿病", "房颤", "高脂血症"], k=random.randint(0, 2)))
        drug_ids = [a, b]

        # 偶尔加第三个安全药物增加干扰
        if random.random() < 0.3:
            safe_drugs = [d["id"] for d in DRUGS if not any(
                tuple(sorted([d["id"], x])) in INTERACTION_MAP for x in drug_ids)]
            if safe_drugs:
                drug_ids.append(random.choice(safe_drugs))

        cases.append({
            "id": _case_id("HI", i + 1),
            "category": "高风险交互",
            "desc": f"{_drug_name(a)}+{_drug_name(b)}({severity}级交互),{age}岁{gender}",
            "drugs": [_drug_name(d) for d in drug_ids],
            "patient": patient,
            "prescription_text": _make_prescription(drug_ids, patient),
            "expected_risk": severity,
            "expected_min_interactions": 1,
            "expected_min_rules": 0,
            "source": f"INTERACTIONS({severity}): {mechanism}",
        })
    return cases


def generate_special_population(n: int = 12) -> list[dict]:
    """特殊人群禁忌用例。"""
    cases = []

    # 孕妇禁忌药物
    pregnancy_danger = ["warfarin", "atorvastatin", "simvastatin", "losartan",
                        "lisinopril", "valproate", "ciprofloxacin", "methotrexate",
                        "isotretinoin", "tretinoin", "doxycycline"]
    random.shuffle(pregnancy_danger)

    for i, drug_id in enumerate(pregnancy_danger[:min(20, max(8, n // 2))]):
        age = random.choice([25, 28, 30, 32, 35])
        patient = _make_patient(age=age, gender="女", pregnancy="yes",
                                conditions=random.sample(["高血压", "癫痫", "高脂血症", "感染"], k=1))
        cases.append({
            "id": _case_id("PG", i + 1),
            "category": "孕妇禁忌",
            "desc": f"{_drug_name(drug_id)},孕妇,{age}岁",
            "drugs": [_drug_name(drug_id)],
            "patient": patient,
            "prescription_text": _make_prescription([drug_id], patient),
            "expected_risk": "critical",
            "expected_min_interactions": 0,
            "expected_min_rules": 1,
            "source": "pregnancy_contraindication",
        })

    # 儿童禁忌
    child_danger = [("ciprofloxacin", "喹诺酮影响软骨发育"),
                    ("aspirin", "Reye综合征"),
                    ("doxycycline", "牙齿着色"),
                    ("tetracycline", "牙齿着色")]
    for i, (drug_id, reason) in enumerate(child_danger[:3]):
        age = random.choice([6, 8, 10, 12])
        patient = _make_patient(age=age, gender=random.choice(["男", "女"]),
                                conditions=["感染"])
        cases.append({
            "id": _case_id("CH", i + 1),
            "category": "儿童禁忌",
            "desc": f"{_drug_name(drug_id)},{age}岁儿童({reason})",
            "drugs": [_drug_name(drug_id)],
            "patient": patient,
            "prescription_text": _make_prescription([drug_id], patient),
            "expected_risk": "critical",
            "expected_min_interactions": 0,
            "expected_min_rules": 1,
            "source": f"age_contraindication: {reason}",
        })

    # 老年人高危
    elderly_danger = [("diazepam", "跌倒风险"), ("alprazolam", "认知障碍"),
                      ("ibuprofen", "消化道出血"), ("digoxin", "中毒风险")]
    for i, (drug_id, reason) in enumerate(elderly_danger[:4]):
        age = random.choice([70, 75, 78, 82])
        patient = _make_patient(age=age, gender=random.choice(["男", "女"]),
                                conditions=random.sample(["高血压", "冠心病", "糖尿病"], k=random.randint(1, 2)))
        cases.append({
            "id": _case_id("EL", i + 1),
            "category": "老年人高危",
            "desc": f"{_drug_name(drug_id)},{age}岁({reason})",
            "drugs": [_drug_name(drug_id)],
            "patient": patient,
            "prescription_text": _make_prescription([drug_id], patient),
            "expected_risk": "high",
            "expected_min_interactions": 0,
            "expected_min_rules": 1,
            "source": f"age_related: {reason}",
        })

    # 肾功能不全
    renal_danger = ["metformin", "lithium", "digoxin"]
    for i, drug_id in enumerate(renal_danger):
        age = random.choice([55, 60, 65])
        patient = _make_patient(age=age, gender=random.choice(["男", "女"]),
                                conditions=["慢性肾病"], renal="impaired")
        cases.append({
            "id": _case_id("RN", i + 1),
            "category": "肾功能不全",
            "desc": f"{_drug_name(drug_id)},肾功能不全,{age}岁",
            "drugs": [_drug_name(drug_id)],
            "patient": patient,
            "prescription_text": _make_prescription([drug_id], patient),
            "expected_risk": "critical",
            "expected_min_interactions": 0,
            "expected_min_rules": 1,
            "source": "renal_impairment",
        })

    return cases[:n]


def generate_medium_risk(n: int = 12) -> list[dict]:
    """中风险组合用例。"""
    medium_pairs = [(a, b, sev, mech) for a, b, sev, mech in INTERACTIONS if sev == "medium"]
    random.shuffle(medium_pairs)

    cases = []
    for i, (a, b, severity, mechanism) in enumerate(medium_pairs[:n]):
        age = random.choice([40, 45, 50, 55, 60])
        gender = random.choice(["男", "女"])
        patient = _make_patient(age=age, gender=gender,
                                conditions=random.sample(["高血压", "糖尿病", "高脂血症", "胃炎"], k=random.randint(0, 2)))
        drug_ids = [a, b]

        cases.append({
            "id": _case_id("MD", i + 1),
            "category": "中风险",
            "desc": f"{_drug_name(a)}+{_drug_name(b)}(medium),{age}岁{gender}",
            "drugs": [_drug_name(d) for d in drug_ids],
            "patient": patient,
            "prescription_text": _make_prescription(drug_ids, patient),
            "expected_risk": "medium",
            "expected_min_interactions": 1,
            "expected_min_rules": 0,
            "source": f"INTERACTIONS(medium): {mechanism}",
        })
    return cases


def generate_safe_cases(n: int = 12) -> list[dict]:
    """安全组合用例:无交互的药物对。"""
    # 找出所有没有交互关系的药物对
    safe_pairs = []
    tested = set()
    for d1 in DRUGS[:60]:  # 从常用药物中取
        for d2 in DRUGS[:60]:
            key = tuple(sorted([d1["id"], d2["id"]]))
            if d1["id"] == d2["id"] or key in tested:
                continue
            tested.add(key)
            if key not in INTERACTION_MAP:
                safe_pairs.append((d1["id"], d2["id"]))

    random.shuffle(safe_pairs)
    cases = []
    for i, (a, b) in enumerate(safe_pairs[:n]):
        age = random.choice([35, 40, 45, 50, 55])
        gender = random.choice(["男", "女"])
        patient = _make_patient(age=age, gender=gender,
                                conditions=random.sample(["高血压", "胃炎", "糖尿病", "过敏", "甲减"], k=random.randint(0, 2)))
        drug_ids = [a, b]

        # 检查规则引擎是否会触发(安全用例不应触发规则)
        from app.rules.safety_rules import run_all_rules
        from app.graph.drug_graph import get_drug_by_name
        drugs_info = []
        for did in drug_ids:
            d = get_drug_by_name(_drug_name(did))
            if d:
                drugs_info.append({"id": d["id"], "name": d["name"]})
        rule_risks = run_all_rules(drugs_info, patient)

        expected_risk = "safe"
        expected_min_rules = 0
        if rule_risks:
            # 如果规则引擎触发了，这个用例不算纯安全
            max_sev = max((_risk_level_num(r["severity"]) for r in rule_risks), default=0)
            if max_sev >= 3:
                expected_risk = "high"
                expected_min_rules = 1
            elif max_sev >= 2:
                expected_risk = "medium"
                expected_min_rules = 1

        cases.append({
            "id": _case_id("SF", i + 1),
            "category": "安全组合",
            "desc": f"{_drug_name(a)}+{_drug_name(b)},{age}岁{gender}(无交互)",
            "drugs": [_drug_name(d) for d in drug_ids],
            "patient": patient,
            "prescription_text": _make_prescription(drug_ids, patient),
            "expected_risk": expected_risk,
            "expected_min_interactions": 0,
            "expected_min_rules": expected_min_rules,
            "source": "no_known_interaction",
        })
    return cases


def generate_edge_cases(n: int = 8) -> list[dict]:
    """边界/陷阱用例:多药联用、复杂场景。"""
    cases = []

    # 多药联用(3-4种药物，有交互链)
    multi_drug_sets = [
        (["warfarin", "aspirin", "ibuprofen"], "critical", "三重出血风险叠加"),
        (["diazepam", "morphine", "alcohol"], "critical", "三重中枢抑制"),
        (["fluoxetine", "tramadol", "linezolid"], "critical", "三重5-HT风险"),
        (["simvastatin", "clarithromycin", "amiodarone"], "critical", "多重CYP3A4抑制"),
        (["metoprolol", "verapamil", "diltiazem"], "critical", "三重心脏抑制"),
        (["lithium", "lisinopril", "ibuprofen"], "high", "锂中毒三重风险"),
    ]

    for i, (drug_ids, expected, desc) in enumerate(multi_drug_sets):
        age = random.choice([55, 60, 65, 70])
        gender = random.choice(["男", "女"])
        patient = _make_patient(age=age, gender=gender,
                                conditions=random.sample(["高血压", "冠心病", "抑郁症", "房颤"], k=random.randint(1, 2)))
        cases.append({
            "id": _case_id("ED", i + 1),
            "category": "多药联用",
            "desc": f"{'+'.join(_drug_name(d) for d in drug_ids)},{age}岁({desc})",
            "drugs": [_drug_name(d) for d in drug_ids],
            "patient": patient,
            "prescription_text": _make_prescription(drug_ids, patient),
            "expected_risk": expected,
            "expected_min_interactions": 2,
            "expected_min_rules": 0,
            "source": f"edge_case: {desc}",
        })

    # 肝功能不全+高危药物
    hepatic_cases = [
        ("warfarin", "critical", "肝功能不全+华法林出血风险"),
        ("atorvastatin", "critical", "肝功能不全+他汀肝毒性"),
    ]
    for i, (drug_id, expected, desc) in enumerate(hepatic_cases):
        age = 58
        patient = _make_patient(age=age, gender="男", conditions=["肝硬化"], liver="impaired")
        cases.append({
            "id": _case_id("ED", len(multi_drug_sets) + i + 1),
            "category": "肝功能不全",
            "desc": f"{_drug_name(drug_id)},肝功能不全({desc})",
            "drugs": [_drug_name(drug_id)],
            "patient": patient,
            "prescription_text": _make_prescription([drug_id], patient),
            "expected_risk": expected,
            "expected_min_interactions": 0,
            "expected_min_rules": 1,
            "source": f"edge_case: {desc}",
        })

    return cases[:n]


def _risk_level_num(level: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "safe": 0}.get(level, -1)


def generate_all(target_total: int = 180) -> list[dict]:
    """生成全部用例。图谱扩容后按更大目标采样。"""
    n_high = min(80, max(30, target_total // 3))
    n_special = min(40, max(16, target_total // 5))
    n_medium = min(40, max(16, target_total // 5))
    n_safe = min(40, max(16, target_total // 5))
    n_edge = min(24, max(10, target_total // 8))

    all_cases = []
    all_cases.extend(generate_high_risk_interactions(n_high))
    all_cases.extend(generate_special_population(n_special))
    all_cases.extend(generate_medium_risk(n_medium))
    all_cases.extend(generate_safe_cases(n_safe))
    all_cases.extend(generate_edge_cases(n_edge))

    # 去重(按 drugs 组合)
    seen = set()
    unique = []
    for c in all_cases:
        key = tuple(sorted(c["drugs"]))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def print_stats(cases: list[dict]):
    """打印统计信息。"""
    categories = {}
    risk_dist = {}
    for c in cases:
        cat = c["category"]
        risk = c["expected_risk"]
        categories[cat] = categories.get(cat, 0) + 1
        risk_dist[risk] = risk_dist.get(risk, 0) + 1

    print(f"\n{'='*50}")
    print(f"[Stats] 生成用例统计")
    print(f"{'='*50}")
    print(f"总计: {len(cases)} 个用例\n")

    print("按类别:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\n按期望风险等级:")
    for risk in ["critical", "high", "medium", "low", "safe"]:
        if risk in risk_dist:
            print(f"  {risk}: {risk_dist[risk]}")

    # 统计药物覆盖
    all_drugs = set()
    for c in cases:
        all_drugs.update(c["drugs"])
    print(f"\n覆盖药物: {len(all_drugs)} 种")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量生成评测用例")
    parser.add_argument("--preview", action="store_true", help="预览前10个用例")
    parser.add_argument("--target", type=int, default=180, help="目标用例总数(默认180)")
    args = parser.parse_args()

    cases = generate_all(args.target)

    if args.preview:
        for c in cases[:10]:
            print(f"\n--- {c['id']}: {c['desc']} ---")
            print(f"  类别: {c['category']}")
            print(f"  期望风险: {c['expected_risk']}")
            print(f"  药物: {', '.join(c['drugs'])}")
            print(f"  来源: {c['source']}")
            print(f"  处方:\n{c['prescription_text']}")
    else:
        # 输出 JSON
        output_path = Path(__file__).resolve().parent.parent / "data" / "eval_cases_generated.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"[OK] 已生成 {len(cases)} 个用例 -> {output_path}")
        print_stats(cases)
