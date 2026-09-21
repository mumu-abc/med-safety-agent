"""安全规则引擎:可配置的高风险规则,不依赖LLM。

面试要点(这是杀手锏):
1. 医疗场景不能完全依赖LLM——LLM可能幻觉、可能遗漏。
2. 关键安全规则硬编码,作为"安全网"兜底。
3. LLM负责"理解和推理",规则引擎负责"不能犯的错"。
4. 两者互补:LLM处理复杂语义,规则引擎保证底线安全。
5. 规则可配置:权重/阈值从 rules_config.json 读取,支持反馈驱动优化。
"""
from app.rules.rule_optimizer import get_rule_weight, get_rule_severity, record_trigger


def check_age_related(drugs: list[dict], age: int | None) -> list[dict]:
    """年龄相关风险。"""
    if age is None:
        return []
    risks = []
    for drug in drugs:
        name = drug.get("name", "")
        drug_id = drug.get("id", "")

        # 老年人风险
        if age >= 65:
            if drug_id in ("diazepam", "alprazolam"):
                risks.append({
                    "drug": name, "risk": "老年人使用苯二氮卓类药物跌倒和认知障碍风险增加",
                    "severity": "high", "rule": "age_benzodiazepine_elderly",
                    "suggestion": "考虑减量或换用非苯二氮卓类药物",
                })
            if drug_id in ("ibuprofen", "diclofenac", "naproxen"):
                risks.append({
                    "drug": name, "risk": "老年人使用NSAIDs消化道出血和肾损伤风险增加",
                    "severity": "high", "rule": "age_nsaid_elderly",
                    "suggestion": "考虑换用对乙酰氨基酚,或加用PPI保护",
                })
            if drug_id == "digoxin":
                risks.append({
                    "drug": name, "risk": "老年人肾功能下降,地高辛中毒风险增加",
                    "severity": "high", "rule": "age_digoxin_elderly",
                    "suggestion": "减量使用,监测血药浓度",
                })

        # 儿童禁忌
        if age < 18:
            if drug_id == "ciprofloxacin":
                risks.append({
                    "drug": name, "risk": "喹诺酮类药物影响儿童软骨发育",
                    "severity": "high", "rule": "age_quinolone_child",
                    "suggestion": "通常避免,换用其他抗生素",
                })
            if drug_id == "aspirin":
                risks.append({
                    "drug": name, "risk": "儿童使用阿司匹林与Reye综合征相关",
                    "severity": "critical", "rule": "age_aspirin_child",
                    "suggestion": "禁止使用,换用对乙酰氨基酚退热",
                })
            if drug_id in ("doxycycline", "minocycline"):
                risks.append({
                    "drug": name, "risk": "四环素类药物影响儿童牙齿和骨骼发育",
                    "severity": "high", "rule": "age_tetracycline_child",
                    "suggestion": "8岁以下禁用,换用其他抗生素",
                })
    return risks


def check_pregnancy(drugs: list[dict], pregnancy: str) -> list[dict]:
    """孕期用药风险。"""
    if pregnancy != "yes":
        return []
    risks = []
    pregnancy_danger = {
        "warfarin": ("X级,致畸", "critical"),
        "atorvastatin": ("X级,致畸", "critical"),
        "simvastatin": ("X级,致畸", "critical"),
        "valproate": ("D级,神经管缺陷", "critical"),
        "carbamazepine": ("D级,致畸", "high"),
        "losartan": ("D级,致畸", "high"),
        "lisinopril": ("D级,致畸", "high"),
        "fluoxetine": ("C级", "medium"),
        "ibuprofen": ("D级(孕晚期),动脉导管早闭", "high"),
        "diclofenac": ("D级(孕晚期)", "high"),
        "ciprofloxacin": ("C级", "medium"),
        "tretinoin": ("X级,致畸", "critical"),
        "isotretinoin": ("X级,致畸(极高风险)", "critical"),
        "methotrexate": ("X级,致畸,流产", "critical"),
    }
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in pregnancy_danger:
            desc, severity = pregnancy_danger[drug_id]
            risks.append({
                "drug": drug.get("name", drug_id),
                "risk": f"孕期禁忌: {desc}",
                "severity": severity,
                "rule": "pregnancy_contraindication",
                "suggestion": "必须停药或换用安全替代药物",
            })
    return risks


def check_renal_impairment(drugs: list[dict], renal: str) -> list[dict]:
    """肾功能不全风险。"""
    if renal != "impaired":
        return []
    risks = []
    renal_risk_drugs = {
        "metformin": ("经肾排泄,肾功能不全时乳酸酸中毒风险", "critical"),
        "furosemide": ("肾功能不全时效果减弱", "medium"),
        "digoxin": ("经肾排泄,需减量", "high"),
        "lithium": ("治疗窗窄,肾功能不全时中毒风险", "critical"),
        "ceftriaxone": ("需调整剂量", "medium"),
        "acyclovir": ("肾毒性,需减量", "high"),
    }
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in renal_risk_drugs:
            desc, severity = renal_risk_drugs[drug_id]
            risks.append({
                "drug": drug.get("name", drug_id),
                "risk": f"肾功能不全: {desc}",
                "severity": severity,
                "rule": "renal_impairment",
                "suggestion": "根据eGFR调整剂量或换药",
            })
    return risks


def check_hepatic_impairment(drugs: list[dict], hepatic: str) -> list[dict]:
    """肝功能不全风险。"""
    if hepatic != "impaired":
        return []
    risks = []
    hepatic_risk_drugs = {
        "warfarin": ("肝功能不全时凝血因子合成减少,出血风险增加", "critical"),
        "atorvastatin": ("他汀类肝毒性,肝功能不全禁用", "critical"),
        "simvastatin": ("他汀类肝毒性,肝功能不全禁用", "critical"),
        "valproate": ("肝毒性,肝功能不全禁用", "critical"),
        "acetaminophen": ("肝代谢,过量肝毒性", "high"),
        "metronidazole": ("肝功能不全时需减量", "medium"),
    }
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in hepatic_risk_drugs:
            desc, severity = hepatic_risk_drugs[drug_id]
            risks.append({
                "drug": drug.get("name", drug_id),
                "risk": f"肝功能不全: {desc}",
                "severity": severity,
                "rule": "hepatic_impairment",
                "suggestion": "禁用或减量,监测肝功能",
            })
    return risks


def check_allergies(drugs: list[dict], allergies: list[str]) -> list[dict]:
    """过敏交叉检查：处方药物是否与患者过敏史冲突。"""
    if not allergies:
        return []

    # 过敏关键词 → 药物 ID 映射
    allergy_drug_map = {
        "青霉素": ["amoxicillin", "ampicillin", "penicillin"],
        "阿莫西林": ["amoxicillin"],
        "磺胺": ["sulfamethoxazole_trimethoprim"],
        "复方磺胺": ["sulfamethoxazole_trimethoprim"],
        "头孢": ["ceftriaxone", "cephalexin", "cefuroxime"],
        "阿司匹林": ["aspirin"],
        "布洛芬": ["ibuprofen"],
        "nsaids": ["ibuprofen", "diclofenac", "naproxen"],
        "非甾体": ["ibuprofen", "diclofenac", "naproxen"],
        "碘": ["contrast_iodine"],
        "造影剂": ["contrast_iodine"],
        "麻醉": ["lidocaine", "propofol"],
        "局麻": ["lidocaine"],
        "链霉素": ["streptomycin"],
        "庆大霉素": ["gentamicin"],
        "氨基糖苷": ["streptomycin", "gentamicin"],
    }

    risks = []
    for allergy in allergies:
        allergy_lower = allergy.lower().strip()
        matched_drug_ids = set()

        # 精确匹配 + 关键词匹配（统一小写比较）
        for keyword, drug_ids in allergy_drug_map.items():
            keyword_lower = keyword.lower()
            if keyword_lower in allergy_lower or allergy_lower in keyword_lower:
                matched_drug_ids.update(drug_ids)

        # 检查处方中是否有匹配药物
        for drug in drugs:
            drug_id = drug.get("id", "")
            drug_name = drug.get("name", "")
            if drug_id in matched_drug_ids:
                risks.append({
                    "drug": drug_name,
                    "risk": f"患者过敏史包含「{allergy}」，与处方药物冲突",
                    "severity": "critical",
                    "rule": "allergy_cross_check",
                    "suggestion": f"立即停用{drug_name}，换用无交叉过敏的替代药物",
                })

    return risks


def check_qt_prolongation(drugs: list[dict]) -> list[dict]:
    """QT间期延长风险：多种药物可延长QT间期，叠加致尖端扭转型室速。"""
    qt_drugs = {
        "ondansetron": ("5-HT3拮抗剂，可延长QT", "high"),
        "haloperidol": ("抗精神病药，QT延长高风险", "critical"),
        "amiodarone": ("III类抗心律失常药，QT延长", "high"),
        "sotalol": ("III类抗心律失常药，QT延长", "high"),
        "erythromycin": ("大环内酯类，QT延长", "high"),
        "clarithromycin": ("大环内酯类，QT延长", "high"),
        "azithromycin": ("大环内酯类，QT延长风险较低", "medium"),
        "ciprofloxacin": ("喹诺酮类，QT延长", "high"),
        "moxifloxacin": ("喹诺酮类，QT延长", "high"),
        "fluoxetine": ("SSRI，QT延长", "medium"),
        "citalopram": ("SSRI，QT延长（剂量依赖）", "high"),
        "escitalopram": ("SSRI，QT延长", "medium"),
        "methadone": ("阿片类，QT延长", "high"),
        "droperidol": ("抗精神病药，QT延长", "high"),
    }

    risks = []
    found_qt = []
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in qt_drugs:
            desc, severity = qt_drugs[drug_id]
            found_qt.append((drug.get("name", drug_id), desc, severity))

    # 单个QT药物 → 警告
    for name, desc, severity in found_qt:
        risks.append({
            "drug": name,
            "risk": f"QT间期延长风险: {desc}",
            "severity": severity,
            "rule": "qt_prolongation",
            "suggestion": "监测心电图，避免联用其他QT延长药物",
        })

    # 多个QT药物叠加 → 升级为critical
    if len(found_qt) >= 2:
        names = [n for n, _, _ in found_qt]
        risks.append({
            "drug": " + ".join(names),
            "risk": f"多种QT延长药物联用，尖端扭转型室速风险显著增加",
            "severity": "critical",
            "rule": "qt_prolongation_stacking",
            "suggestion": "必须更换其中至少一种药物，避免QT延长药物叠加",
        })

    return risks


def check_bleeding_risk(drugs: list[dict], patient: dict) -> list[dict]:
    """出血风险：抗凝/抗血小板/NSAIDs叠加，或与出血性疾病共存。"""
    anticoagulants = {"warfarin", "rivaroxaban", "apixaban", "edoxaban", "dabigatran", "enoxaparin"}
    antiplatelets = {"aspirin", "clopidogrel", "ticagrelor", "prasugrel"}
    nsaids = {"ibuprofen", "diclofenac", "naproxen", "meloxicam", "celecoxib"}

    found_anticoag = []
    found_antiplate = []
    found_nsaid = []

    for drug in drugs:
        drug_id = drug.get("id", "")
        drug_name = drug.get("name", drug_id)
        if drug_id in anticoagulants:
            found_anticoag.append(drug_name)
        elif drug_id in antiplatelets:
            found_antiplate.append(drug_name)
        elif drug_id in nsaids:
            found_nsaid.append(drug_name)

    risks = []
    active_count = len(found_anticoag) + len(found_antiplate)

    # 双联抗栓
    if len(found_anticoag) >= 1 and len(found_antiplate) >= 1:
        risks.append({
            "drug": " + ".join(found_anticoag + found_antiplate),
            "risk": "抗凝+抗血小板双联治疗，消化道出血风险增加3-4倍",
            "severity": "high",
            "rule": "bleeding_dual_antiplatelet",
            "suggestion": "评估出血风险(HAS-BLED评分)，考虑加用PPI保护",
        })

    # 三联抗栓
    if len(found_anticoag) >= 1 and len(found_antiplate) >= 2:
        risks.append({
            "drug": " + ".join(found_anticoag + found_antiplate),
            "risk": "三联抗栓治疗，出血风险极高",
            "severity": "critical",
            "rule": "bleeding_triple_therapy",
            "suggestion": "尽量缩短三联疗程，评估是否可降级为双联",
        })

    # 抗凝/抗血小板 + NSAIDs
    if active_count >= 1 and found_nsaid:
        risks.append({
            "drug": " + ".join(found_anticoag + found_antiplate + found_nsaid),
            "risk": "抗栓药物+NSAIDs，消化道出血风险显著增加",
            "severity": "high",
            "rule": "bleeding_nsaid_combined",
            "suggestion": "避免联用，必须联用时加用PPI",
        })

    return risks


def check_cns_depression(drugs: list[dict]) -> list[dict]:
    """CNS抑制风险：多种中枢抑制药物叠加可致呼吸抑制。"""
    cns_drugs = {
        "diazepam": ("苯二氮卓类", "high"),
        "alprazolam": ("苯二氮卓类", "high"),
        "lorazepam": ("苯二氮卓类", "high"),
        "midazolam": ("苯二氮卓类", "high"),
        "morphine": ("阿片类镇痛药", "high"),
        "oxycodone": ("阿片类镇痛药", "high"),
        "tramadol": ("弱阿片类", "high"),
        "fentanyl": ("强效阿片类", "critical"),
        "codeine": ("阿片类", "medium"),
        "gabapentin": ("抗惊厥药，CNS抑制", "medium"),
        "pregabalin": ("抗惊厥药，CNS抑制", "medium"),
        "zolpidem": ("非苯二氮卓类催眠药", "high"),
        "zopiclone": ("非苯二氮卓类催眠药", "high"),
        "quetiapine": ("抗精神病药，镇静", "medium"),
        "promethazine": ("抗组胺药，镇静", "medium"),
        "diphenhydramine": ("抗组胺药，镇静", "medium"),
    }

    risks = []
    found_cns = []
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in cns_drugs:
            desc, severity = cns_drugs[drug_id]
            found_cns.append((drug.get("name", drug_id), desc, severity, drug_id))

    # 多种CNS抑制药物叠加
    if len(found_cns) >= 2:
        names = [n for n, _, _, _ in found_cns]
        max_severity = "critical" if any(s == "critical" for _, _, s, _ in found_cns) else "high"
        risks.append({
            "drug": " + ".join(names),
            "risk": f"多种中枢抑制药物联用，呼吸抑制和过度镇静风险",
            "severity": max_severity,
            "rule": "cns_depression_stacking",
            "suggestion": "减少CNS抑制药物种类，监测呼吸频率和意识状态",
        })

    # 阿片类 + 苯二氮卓（FDA 黑框警告）
    has_opioid = any(d_id in ("morphine", "oxycodone", "fentanyl", "tramadol", "codeine") for _, _, _, d_id in found_cns)
    has_benzo = any(d_id in ("diazepam", "alprazolam", "lorazepam", "midazolam") for _, _, _, d_id in found_cns)
    if has_opioid and has_benzo:
        risks.append({
            "drug": "阿片类 + 苯二氮卓",
            "risk": "FDA黑框警告：阿片类+苯二氮卓联用可致深度镇静、呼吸抑制、昏迷、死亡",
            "severity": "critical",
            "rule": "cns_opioid_benzo_blackbox",
            "suggestion": "尽量避免联用，必须联用时减量并密切监测",
        })

    return risks


def check_serotonin_syndrome(drugs: list[dict]) -> list[dict]:
    """5-HT综合征风险：多种升5-HT药物叠加。"""
    serotonergic = {
        "fluoxetine": ("SSRI", "high"),
        "sertraline": ("SSRI", "high"),
        "paroxetine": ("SSRI", "high"),
        "citalopram": ("SSRI", "high"),
        "escitalopram": ("SSRI", "high"),
        "venlafaxine": ("SNRI", "high"),
        "duloxetine": ("SNRI", "high"),
        "tramadol": ("弱阿片类（也有5-HT作用）", "high"),
        "linezolid": ("抗生素（MAOI活性）", "critical"),
        "methylene_blue": ("MAOI活性", "critical"),
        "selegiline": ("MAO-B抑制剂", "high"),
        "moclobemide": ("MAOI", "critical"),
        "buspirone": ("5-HT1A激动剂", "medium"),
        "sumatriptan": ("5-HT1B/1D激动剂", "medium"),
        "ondansetron": ("5-HT3拮抗剂", "low"),
    }

    risks = []
    found_sero = []
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in serotonergic:
            desc, severity = serotonergic[drug_id]
            found_sero.append((drug.get("name", drug_id), desc, severity))

    # SSRI/SNRI + MAOI → 绝对禁忌
    has_ssri_snri = any("SSRI" in d or "SNRI" in d for _, d, _ in found_sero)
    has_maoi = any("MAOI" in d or "MAO" in d for _, d, _ in found_sero)
    if has_ssri_snri and has_maoi:
        risks.append({
            "drug": "SSRI/SNRI + MAOI",
            "risk": "5-HT综合征绝对禁忌：可致高热、肌阵挛、意识障碍、死亡",
            "severity": "critical",
            "rule": "serotonin_ssri_maoi",
            "suggestion": "绝对禁止联用，MAOI停药至少2周后才能换用SSRI",
        })

    # 多种升5-HT药物
    if len(found_sero) >= 2 and not (has_ssri_snri and has_maoi):
        names = [n for n, _, _ in found_sero]
        risks.append({
            "drug": " + ".join(names),
            "risk": "多种5-HT能药物联用，5-HT综合征风险",
            "severity": "high",
            "rule": "serotonin_stacking",
            "suggestion": "监测5-HT综合征症状（震颤、肌阵挛、高热、腹泻）",
        })

    return risks


def check_anticholinergic_burden(drugs: list[dict], age: int | None) -> list[dict]:
    """老年人抗胆碱能负荷叠加。

    为什么需要这条规则（图谱覆盖不到的部分）：
        药物图谱是按"药物对"存边的，它只能回答"这两味药有没有已知相互作用"。
        但抗胆碱能副作用是**剂量/种类累加**的 —— 三味各自"轻微抗胆碱能"的药
        （阿米替林 + 苯扎托品 + 氯苯那敏）联用后，总抗胆碱能负荷可能很高，
        而任意两味之间的边在药理教材里根本不存在，图谱查不到任何东西。
        这是"单药都不危险、联用才危险"的典型场景，只能靠规则层按**计数**兜住。

    临床后果（老年人尤其显著）：
        认知障碍/谵妄、跌倒、便秘、尿潴留、口干、视物模糊。
        老年人抗胆碱能负荷过高与住院率、死亡率上升相关（Beers 标准重点关注）。

    分级依据（按抗胆碱能强度加权，非简单计数）：
        strong(3分)  —— 明确的强抗胆碱能药
        moderate(2分) —— 中度
        mild(1分)     —— 较弱 / 第二代抗组胺药
        年龄阈值 65 岁（与 check_age_related 保持一致）。
    """
    if age is None or age < 65:
        return []

    # 抗胆碱能强度分级（依据抗胆碱能负荷量表 Anticholinergic Burden Scale 常用分级）
    anticholinergic_scale = {
        # --- strong: 3 ---
        "amitriptyline": ("阿米替林", 3),
        "clomipramine": ("氯米帕明", 3),
        "imipramine": ("丙咪嗪", 3),
        "doxepin": ("多塞平", 3),
        "chlorpromazine": ("氯丙嗪", 3),
        "clozapine": ("氯氮平", 3),
        "benztropine": ("苯扎托品", 3),
        "trihexyphenidyl": ("苯海索", 3),
        "atropine": ("阿托品", 3),
        "scopolamine": ("东莨菪碱", 3),
        "chlorpheniramine": ("氯苯那敏", 3),
        # --- moderate: 2 ---
        "nortriptyline": ("去甲替林", 2),
        "olanzapine": ("奥氮平", 2),
        "quetiapine": ("喹硫平", 2),
        "promethazine": ("异丙嗪", 2),
        "hydroxyzine": ("羟嗪", 2),
        "meclizine": ("美克洛嗪", 2),
        "dimenhydrinate": ("茶苯海明", 2),
        "glycopyrrolate": ("格隆溴铵", 2),
        # --- mild: 1 ---
        "cetirizine": ("西替利嗪", 1),
        "loratadine": ("氯雷他定", 1),
        "ipratropium": ("异丙托溴铵", 1),   # 吸入,全身吸收少
        "tiotropium": ("噻托溴铵", 1),      # 吸入,全身吸收少
    }

    found = []
    for drug in drugs:
        drug_id = drug.get("id", "")
        if drug_id in anticholinergic_scale:
            name, score = anticholinergic_scale[drug_id]
            found.append((drug.get("name", name) or name, drug_id, score))

    if not found:
        return []

    total_burden = sum(s for _, _, s in found)
    names = " + ".join(n for n, _, _ in found)

    # ── 判定：≥3 分算有临床意义的负荷 ──
    # 单药 strong(3分) 也报，但等级较低；多药叠加升级。
    if total_burden < 3:
        return []

    if total_burden >= 6:
        severity = "critical"
        summary = "抗胆碱能负荷显著偏高"
        suggestion = "必须精简用药：优先停用抗胆碱能作用最强的一种，换用替代药物"
    elif total_burden >= 4:
        severity = "high"
        summary = "抗胆碱能负荷偏高"
        suggestion = "评估每种药物的必要性，能停则停；优先替换抗胆碱能作用强的药物"
    else:  # total_burden in (3,) —— 单药强抗胆碱能，或 3 味 mild 叠加
        severity = "medium"
        summary = "存在抗胆碱能负荷"
        suggestion = "监测认知功能、排便和排尿情况；避免再加用其他抗胆碱能药物"

    detail = "、".join(f"{n}({s}分)" for n, _, s in found)

    return [{
        "drug": names,
        "risk": (
            f"{summary}（累计 {total_burden} 分）：{detail}。"
            f"老年人抗胆碱能负荷叠加可致认知障碍/谵妄、跌倒、便秘、尿潴留"
        ),
        "severity": severity,
        "rule": "anticholinergic_burden_elderly",
        "suggestion": suggestion,
    }]


def run_all_rules(drugs: list[dict], patient: dict) -> list[dict]:
    """运行所有安全规则（10 类）,应用动态权重。"""
    all_risks = []
    all_risks.extend(check_age_related(drugs, patient.get("age")))
    all_risks.extend(check_pregnancy(drugs, patient.get("pregnancy", "no")))
    all_risks.extend(check_renal_impairment(drugs, patient.get("renal_function", "normal")))
    all_risks.extend(check_hepatic_impairment(drugs, patient.get("liver_function", "normal")))
    all_risks.extend(check_allergies(drugs, patient.get("allergies", [])))
    all_risks.extend(check_qt_prolongation(drugs))
    all_risks.extend(check_bleeding_risk(drugs, patient))
    all_risks.extend(check_cns_depression(drugs))
    all_risks.extend(check_serotonin_syndrome(drugs))
    all_risks.extend(check_anticholinergic_burden(drugs, patient.get("age")))

    # 应用动态权重:记录触发次数,附加权重信息
    for risk in all_risks:
        rule_name = risk.get("rule", "")
        weight = get_rule_weight(rule_name)
        risk["weight"] = weight
        # 如果权重极低(被优化器降级),标记为降级
        if weight < 0.5:
            risk["downgraded"] = True
        record_trigger(rule_name)

    return all_risks


def calculate_risk_score(risks: list[dict]) -> float:
    """计算加权风险评分(0-100)。

    面试要点:不是简单计数,而是根据规则权重和严重程度加权计算。
    权重来自反馈优化器——高频误报的规则权重降低,漏报的规则权重升高。
    """
    severity_scores = {"critical": 40, "high": 25, "medium": 15, "low": 5}
    if not risks:
        return 0.0

    total = 0.0
    for risk in risks:
        sev = risk.get("severity", "medium")
        base = severity_scores.get(sev, 10)
        weight = risk.get("weight", 1.0)
        total += base * weight

    return min(100.0, total)
