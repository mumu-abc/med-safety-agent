"""测试用药安全审查流程。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.drug_data import build_graph_from_data
from app.graph.drug_graph import get_drug_by_name, find_interactions, find_contraindications
from app.rules.safety_rules import run_all_rules


def test_graph_build():
    """测试图谱构建。"""
    stats = build_graph_from_data()
    assert stats["drugs"] > 50, f"药物数量太少: {stats['drugs']}"
    assert stats["interactions"] > 30, f"相互作用太少: {stats['interactions']}"
    print(f"✅ 图谱构建成功: {stats['drugs']} 种药物, {stats['interactions']} 条相互作用")


def test_drug_lookup():
    """测试药物查询。"""
    warfarin = get_drug_by_name("华法林")
    assert warfarin is not None, "华法林未找到"
    assert warfarin["category"] == "抗凝药"
    assert "活动性出血" in warfarin.get("contraindications", [])
    print(f"✅ 药物查询正常: {warfarin['name']} ({warfarin['category']})")


def test_interaction_detection():
    """测试相互作用检测。"""
    warfarin = get_drug_by_name("华法林")
    aspirin = get_drug_by_name("阿司匹林")
    ibuprofen = get_drug_by_name("布洛芬")

    interactions = find_interactions([warfarin["id"], aspirin["id"], ibuprofen["id"]])
    assert len(interactions) >= 2, f"相互作用检测不足: {len(interactions)}"

    severities = {i["severity"] for i in interactions}
    assert "critical" in severities, "缺少 critical 级别相互作用"
    print(f"✅ 相互作用检测正常: {len(interactions)} 条, 严重程度: {severities}")


def test_contraindication_check():
    """测试禁忌症检查。"""
    warfarin = get_drug_by_name("华法林")
    matches = find_contraindications(warfarin["id"], ["孕妇", "活动性出血"])
    assert len(matches) >= 1, "禁忌症检查未命中"
    print(f"✅ 禁忌症检查正常: {len(matches)} 项匹配")


def test_safety_rules():
    """测试安全规则引擎。"""
    drugs = [
        {"id": "ciprofloxacin", "name": "环丙沙星"},
        {"id": "aspirin", "name": "阿司匹林"},
    ]
    patient = {"age": 10, "pregnancy": "no", "renal_function": "normal", "liver_function": "normal"}
    risks = run_all_rules(drugs, patient)
    assert len(risks) >= 1, "安全规则未触发"
    rule_names = {r["rule"] for r in risks}
    assert "age_quinolone_child" in rule_names, "喹诺酮儿童禁忌规则未触发"
    print(f"✅ 安全规则引擎正常: {len(risks)} 项风险, 规则: {rule_names}")


def test_pregnancy_rules():
    """测试孕期用药规则。"""
    drugs = [
        {"id": "warfarin", "name": "华法林"},
        {"id": "losartan", "name": "氯沙坦"},
    ]
    patient = {"age": 28, "pregnancy": "yes", "renal_function": "normal", "liver_function": "normal"}
    risks = run_all_rules(drugs, patient)
    assert len(risks) >= 2, "孕期规则未充分触发"
    print(f"✅ 孕期规则正常: {len(risks)} 项风险")


def test_qt_prolongation():
    """QT间期延长规则。"""
    from app.rules.safety_rules import check_qt_prolongation
    drugs = [
        {"id": "ondansetron", "name": "昂丹司琼"},
        {"id": "haloperidol", "name": "氟哌啶醇"},
    ]
    risks = check_qt_prolongation(drugs)
    assert len(risks) >= 2, "QT延长规则未充分触发"
    rules = {r["rule"] for r in risks}
    assert "qt_prolongation_stacking" in rules, "QT叠加规则未触发"
    print(f"✅ QT延长规则正常: {len(risks)} 项风险")


def test_bleeding_risk():
    """出血风险规则。"""
    from app.rules.safety_rules import check_bleeding_risk
    drugs = [
        {"id": "warfarin", "name": "华法林"},
        {"id": "aspirin", "name": "阿司匹林"},
        {"id": "ibuprofen", "name": "布洛芬"},
    ]
    patient = {}
    risks = check_bleeding_risk(drugs, patient)
    assert len(risks) >= 2, "出血风险规则未充分触发"
    rules = {r["rule"] for r in risks}
    assert "bleeding_dual_antiplatelet" in rules, "双联抗栓规则未触发"
    assert "bleeding_nsaid_combined" in rules, "NSAIDs联用规则未触发"
    print(f"✅ 出血风险规则正常: {len(risks)} 项风险")


def test_cns_depression():
    """CNS抑制风险规则。"""
    from app.rules.safety_rules import check_cns_depression
    drugs = [
        {"id": "morphine", "name": "吗啡"},
        {"id": "diazepam", "name": "地西泮"},
    ]
    risks = check_cns_depression(drugs)
    assert len(risks) >= 2, "CNS抑制规则未充分触发"
    rules = {r["rule"] for r in risks}
    assert "cns_opioid_benzo_blackbox" in rules, "FDA黑框警告规则未触发"
    print(f"✅ CNS抑制规则正常: {len(risks)} 项风险")


def test_serotonin_syndrome():
    """5-HT综合征规则。"""
    from app.rules.safety_rules import check_serotonin_syndrome
    drugs = [
        {"id": "fluoxetine", "name": "氟西汀"},
        {"id": "linezolid", "name": "利奈唑胺"},
    ]
    risks = check_serotonin_syndrome(drugs)
    assert len(risks) >= 1, "5-HT综合征规则未触发"
    rules = {r["rule"] for r in risks}
    assert "serotonin_ssri_maoi" in rules, "SSRI+MAOI禁忌规则未触发"
    print(f"✅ 5-HT综合征规则正常: {len(risks)} 项风险")


def test_all_rules_count():
    """规则引擎应覆盖 9 类规则。"""
    # 测试所有规则类别都能被触发
    drugs = [
        {"id": "warfarin", "name": "华法林"},       # 抗凝
        {"id": "aspirin", "name": "阿司匹林"},       # 抗血小板
        {"id": "ibuprofen", "name": "布洛芬"},       # NSAID
        {"id": "morphine", "name": "吗啡"},          # 阿片类
        {"id": "diazepam", "name": "地西泮"},        # 苯二氮卓
        {"id": "fluoxetine", "name": "氟西汀"},      # SSRI
        {"id": "ciprofloxacin", "name": "环丙沙星"},  # QT延长
    ]
    patient = {"age": 70, "pregnancy": "no", "renal_function": "normal", "liver_function": "normal",
               "allergies": ["青霉素"]}
    risks = run_all_rules(drugs, patient)
    rule_names = {r["rule"] for r in risks}
    # 应该触发多个维度的规则
    assert len(rule_names) >= 5, f"规则覆盖不足: {rule_names}"
    print(f"✅ 规则引擎覆盖: {len(rule_names)} 条规则, {len(risks)} 项风险")


def test_allergen_cross_check():
    """过敏交叉检查。"""
    from app.rules.safety_rules import check_allergies
    drugs = [{"id": "amoxicillin", "name": "阿莫西林"}]
    risks = check_allergies(drugs, ["青霉素"])
    assert len(risks) >= 1
    assert risks[0]["severity"] == "critical"


def test_allergen_no_match():
    """过敏不匹配应无风险。"""
    from app.rules.safety_rules import check_allergies
    drugs = [{"id": "amoxicillin", "name": "阿莫西林"}]
    risks = check_allergies(drugs, ["磺胺"])
    assert len(risks) == 0


def test_allergen_empty_list():
    """空过敏列表应无风险。"""
    from app.rules.safety_rules import check_allergies
    drugs = [{"id": "amoxicillin", "name": "阿莫西林"}]
    risks = check_allergies(drugs, [])
    assert len(risks) == 0


def test_age_boundary_65():
    """65岁边界:刚好65应触发老年人规则。"""
    from app.rules.safety_rules import check_age_related
    drugs = [{"id": "diazepam", "name": "地西泮"}]
    risks = check_age_related(drugs, 65)
    assert len(risks) >= 1


def test_age_boundary_64():
    """64岁不应触发老年人规则。"""
    from app.rules.safety_rules import check_age_related
    drugs = [{"id": "diazepam", "name": "地西泮"}]
    risks = check_age_related(drugs, 64)
    assert len(risks) == 0


def test_age_child_boundary():
    """17岁应触发儿童规则。"""
    from app.rules.safety_rules import check_age_related
    drugs = [{"id": "ciprofloxacin", "name": "环丙沙星"}]
    risks = check_age_related(drugs, 17)
    assert len(risks) >= 1


def test_pregnancy_no():
    """非孕妇不应触发孕期规则。"""
    from app.rules.safety_rules import check_pregnancy
    drugs = [{"id": "warfarin", "name": "华法林"}]
    risks = check_pregnancy(drugs, "no")
    assert len(risks) == 0


def test_renal_normal():
    """肾功能正常不应触发规则。"""
    from app.rules.safety_rules import check_renal_impairment
    drugs = [{"id": "metformin", "name": "二甲双胍"}]
    risks = check_renal_impairment(drugs, "normal")
    assert len(risks) == 0


def test_hepatic_normal():
    """肝功能正常不应触发规则。"""
    from app.rules.safety_rules import check_hepatic_impairment
    drugs = [{"id": "warfarin", "name": "华法林"}]
    risks = check_hepatic_impairment(drugs, "normal")
    assert len(risks) == 0


def test_qt_single_drug():
    """单个QT药物应触发警告但不触发叠加。"""
    from app.rules.safety_rules import check_qt_prolongation
    drugs = [{"id": "ondansetron", "name": "昂丹司琼"}]
    risks = check_qt_prolongation(drugs)
    assert len(risks) >= 1
    rules = {r["rule"] for r in risks}
    assert "qt_prolongation" in rules
    assert "qt_prolongation_stacking" not in rules


def test_cns_single_drug():
    """单个CNS药物不应触发叠加规则。"""
    from app.rules.safety_rules import check_cns_depression
    drugs = [{"id": "morphine", "name": "吗啡"}]
    risks = check_cns_depression(drugs)
    # 单药不触发叠加
    stacking = [r for r in risks if r["rule"] == "cns_depression_stacking"]
    assert len(stacking) == 0


def test_serotonin_single_drug():
    """单个5-HT药物不应触发叠加规则。"""
    from app.rules.safety_rules import check_serotonin_syndrome
    drugs = [{"id": "fluoxetine", "name": "氟西汀"}]
    risks = check_serotonin_syndrome(drugs)
    stacking = [r for r in risks if r["rule"] == "serotonin_stacking"]
    assert len(stacking) == 0


def test_bleeding_no_anticoag():
    """无抗凝药物不应触发出血规则。"""
    from app.rules.safety_rules import check_bleeding_risk
    drugs = [{"id": "amoxicillin", "name": "阿莫西林"}]
    risks = check_bleeding_risk(drugs, {})
    assert len(risks) == 0


def test_run_all_rules_weight_field():
    """run_all_rules 应附加 weight 字段。"""
    drugs = [{"id": "warfarin", "name": "华法林"}]
    patient = {"age": 28, "pregnancy": "yes", "renal_function": "normal", "liver_function": "normal"}
    risks = run_all_rules(drugs, patient)
    for r in risks:
        assert "weight" in r
        assert isinstance(r["weight"], (int, float))


if __name__ == "__main__":
    test_graph_build()
    test_drug_lookup()
    test_interaction_detection()
    test_contraindication_check()
    test_safety_rules()
    test_pregnancy_rules()
    test_qt_prolongation()
    test_bleeding_risk()
    test_cns_depression()
    test_serotonin_syndrome()
    test_all_rules_count()
    print("\n🎉 所有测试通过!")
