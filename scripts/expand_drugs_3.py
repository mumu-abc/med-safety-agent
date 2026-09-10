"""第三批扩展:肿瘤靶向药+免疫治疗,补齐到500+。"""
import sys, importlib
sys.path.insert(0, ".")
import app.graph.drug_data as dd
importlib.reload(dd)

existing_ids = {d["id"] for d in dd.DRUGS}
print(f"Current unique: {len(existing_ids)}")

EXTRAS = [
    {"id": "trastuzumab", "name": "曲妥珠单抗", "category": "生物制剂", "generic_name": "曲妥珠单抗",
     "contraindications": ["对本品过敏"], "side_effects": ["心脏毒性", "输液反应"], "metabolism": "蛋白水解"},
    {"id": "bevacizumab", "name": "贝伐珠单抗", "category": "生物制剂", "generic_name": "贝伐珠单抗",
     "contraindications": ["近期手术", "出血"], "side_effects": ["高血压", "蛋白尿", "出血"], "metabolism": "蛋白水解"},
    {"id": "pembrolizumab", "name": "帕博利珠单抗", "category": "免疫检查点抑制剂",
     "generic_name": "帕博利珠单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应", "肺炎", "肝炎"], "metabolism": "蛋白水解"},
    {"id": "nivolumab", "name": "纳武利尤单抗", "category": "免疫检查点抑制剂",
     "generic_name": "纳武利尤单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应", "肺炎"], "metabolism": "蛋白水解"},
    {"id": "atezolizumab", "name": "阿替利珠单抗", "category": "免疫检查点抑制剂",
     "generic_name": "阿替利珠单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应"], "metabolism": "蛋白水解"},
    {"id": "durvalumab", "name": "度伐利尤单抗", "category": "免疫检查点抑制剂",
     "generic_name": "度伐利尤单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应"], "metabolism": "蛋白水解"},
    {"id": "avelumab", "name": "阿维鲁单抗", "category": "免疫检查点抑制剂",
     "generic_name": "阿维鲁单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应", "输液反应"], "metabolism": "蛋白水解"},
    {"id": "ipilimumab", "name": "伊匹木单抗", "category": "免疫检查点抑制剂",
     "generic_name": "伊匹木单抗", "contraindications": ["对本品过敏"],
     "side_effects": ["免疫相关不良反应(较重)", "结肠炎"], "metabolism": "蛋白水解"},
    {"id": "olaparib", "name": "奥拉帕利", "category": "PARP抑制剂", "generic_name": "奥拉帕利",
     "contraindications": ["严重肝功能不全"], "side_effects": ["骨髓抑制", "恶心"], "metabolism": "CYP3A4"},
    {"id": "niraparib", "name": "尼拉帕利", "category": "PARP抑制剂", "generic_name": "尼拉帕利",
     "contraindications": ["对本品过敏"], "side_effects": ["骨髓抑制", "高血压"], "metabolism": "CYP3A4"},
    {"id": "rucaparib", "name": "卢卡帕利", "category": "PARP抑制剂", "generic_name": "卢卡帕利",
     "contraindications": ["对本品过敏"], "side_effects": ["骨髓抑制", "恶心"], "metabolism": "CYP2D6"},
    {"id": "palbociclib", "name": "哌柏西利", "category": "CDK4/6抑制剂", "generic_name": "哌柏西利",
     "contraindications": ["严重肝功能不全"], "side_effects": ["骨髓抑制", "疲劳"], "metabolism": "CYP3A4"},
    {"id": "ribociclib", "name": "瑞波西利", "category": "CDK4/6抑制剂", "generic_name": "琥珀酸瑞波西利",
     "contraindications": ["QT延长"], "side_effects": ["骨髓抑制", "QT延长"], "metabolism": "CYP3A4"},
    {"id": "abemaciclib", "name": "阿贝西利", "category": "CDK4/6抑制剂", "generic_name": "阿贝西利",
     "contraindications": ["严重肝功能不全"], "side_effects": ["腹泻", "骨髓抑制"], "metabolism": "CYP3A4"},
    {"id": "ibrutinib", "name": "伊布替尼", "category": "BTK抑制剂", "generic_name": "伊布替尼",
     "contraindications": ["CYP3A4强抑制剂合用"], "side_effects": ["出血", "感染", "房颤"], "metabolism": "CYP3A4"},
    {"id": "acalabrutinib", "name": "阿卡替尼", "category": "BTK抑制剂", "generic_name": "阿卡替尼",
     "contraindications": ["CYP3A4强抑制剂合用"], "side_effects": ["头痛", "感染"], "metabolism": "CYP3A4"},
    {"id": "zanubrutinib", "name": "泽布替尼", "category": "BTK抑制剂", "generic_name": "泽布替尼",
     "contraindications": ["CYP3A4强抑制剂合用"], "side_effects": ["感染", "出血"], "metabolism": "CYP3A4"},
    {"id": "venetoclax", "name": "维奈克拉", "category": "BCL-2抑制剂", "generic_name": "维奈克拉",
     "contraindications": ["CYP3A4强抑制剂合用(首剂)"], "side_effects": ["肿瘤溶解综合征", "骨髓抑制"], "metabolism": "CYP3A4"},
    {"id": "enzalutamide", "name": "恩杂鲁胺", "category": "AR抑制剂", "generic_name": "恩杂鲁胺",
     "contraindications": ["对本品过敏"], "side_effects": ["疲劳", "潮热", "癫痫"], "metabolism": "CYP2C8/CYP3A4"},
    {"id": "abiraterone", "name": "阿比特龙", "category": "CYP17抑制剂", "generic_name": "醋酸阿比特龙",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高血压", "低钾血症"], "metabolism": "CYP3A4"},
    {"id": "bortezomib", "name": "硼替佐米", "category": "蛋白酶体抑制剂", "generic_name": "硼替佐米",
     "contraindications": ["对本品过敏"], "side_effects": ["周围神经病变", "血小板减少"], "metabolism": "CYP3A4"},
    {"id": "lenalidomide", "name": "来那度胺", "category": "免疫调节剂", "generic_name": "来那度胺",
     "contraindications": ["孕妇(致畸)"], "side_effects": ["骨髓抑制", "血栓栓塞"], "metabolism": "不代谢"},
    {"id": "pomalidomide", "name": "泊马度胺", "category": "免疫调节剂", "generic_name": "泊马度胺",
     "contraindications": ["孕妇(致畸)"], "side_effects": ["骨髓抑制", "血栓栓塞"], "metabolism": "CYP1A2"},
    {"id": "crizotinib", "name": "克唑替尼", "category": "ALK/ROS1抑制剂", "generic_name": "克唑替尼",
     "contraindications": ["QT延长"], "side_effects": ["视力障碍", "QT延长"], "metabolism": "CYP3A4"},
    {"id": "alectinib", "name": "阿来替尼", "category": "ALK抑制剂", "generic_name": "盐酸阿来替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["肌痛", "便秘"], "metabolism": "CYP3A4"},
    {"id": "osimertinib", "name": "奥希替尼", "category": "EGFR抑制剂", "generic_name": "甲磺酸奥希替尼",
     "contraindications": ["QT延长"], "side_effects": ["皮疹", "腹泻", "间质性肺炎"], "metabolism": "CYP3A4"},
    {"id": "dabrafenib", "name": "达拉非尼", "category": "BRAF抑制剂", "generic_name": "甲磺酸达拉非尼",
     "contraindications": ["对本品过敏"], "side_effects": ["发热", "皮疹"], "metabolism": "CYP2C8"},
    {"id": "trametinib", "name": "曲美替尼", "category": "MEK抑制剂", "generic_name": "曲美替尼",
     "contraindications": ["LVEF降低"], "side_effects": ["皮疹", "腹泻", "心肌病"], "metabolism": "CYP酶(少量)"},
    {"id": "vemurafenib", "name": "维莫非尼", "category": "BRAF抑制剂", "generic_name": "维莫非尼",
     "contraindications": ["QT延长"], "side_effects": ["关节痛", "皮疹"], "metabolism": "CYP3A4"},
    {"id": "regorafenib", "name": "瑞戈非尼", "category": "多激酶抑制剂", "generic_name": "瑞戈非尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["手足综合征", "肝毒性"], "metabolism": "CYP3A4"},
    {"id": "cabozantinib", "name": "卡博替尼", "category": "多激酶抑制剂", "generic_name": "苹果酸卡博替尼",
     "contraindications": ["近期出血"], "side_effects": ["腹泻", "高血压"], "metabolism": "CYP3A4"},
    {"id": "apatinib", "name": "阿帕替尼", "category": "VEGFR抑制剂", "generic_name": "甲磺酸阿帕替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高血压", "蛋白尿"], "metabolism": "CYP3A4"},
    {"id": "anlotinib", "name": "安罗替尼", "category": "多激酶抑制剂", "generic_name": "盐酸安罗替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高血压", "手足综合征"], "metabolism": "CYP1A2"},
    {"id": "surufatinib", "name": "索凡替尼", "category": "多激酶抑制剂", "generic_name": "索凡替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["蛋白尿", "高血压"], "metabolism": "CYP3A4"},
    {"id": "famitinib", "name": "法米替尼", "category": "多激酶抑制剂", "generic_name": "法米替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高血压", "腹泻"], "metabolism": "CYP3A4"},
    {"id": "tivozanib", "name": "替沃扎尼", "category": "VEGFR抑制剂", "generic_name": "替沃扎尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高血压", "疲劳"], "metabolism": "CYP3A4"},
    {"id": "pazopanib", "name": "帕唑帕尼", "category": "多激酶抑制剂", "generic_name": "帕唑帕尼",
     "contraindications": ["QT延长"], "side_effects": ["肝毒性", "高血压", "腹泻"], "metabolism": "CYP3A4"},
    {"id": "sunitinib", "name": "舒尼替尼", "category": "多激酶抑制剂", "generic_name": "苹果酸舒尼替尼",
     "contraindications": ["QT延长"], "side_effects": ["疲劳", "高血压", "手足综合征"], "metabolism": "CYP3A4"},
    {"id": "lapatinib", "name": "拉帕替尼", "category": "HER2/EGFR抑制剂", "generic_name": "甲苯磺酸拉帕替尼",
     "contraindications": ["QT延长"], "side_effects": ["腹泻", "皮疹", "QT延长"], "metabolism": "CYP3A4"},
    {"id": "neratinib", "name": "奈拉替尼", "category": "HER2抑制剂", "generic_name": "马来酸奈拉替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["腹泻", "肝毒性"], "metabolism": "CYP3A4"},
    {"id": "tucatinib", "name": "图卡替尼", "category": "HER2抑制剂", "generic_name": "图卡替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["腹泻", "手足综合征"], "metabolism": "CYP2C8/CYP3A4"},
    {"id": "pirtobrutinib", "name": "吡托布鲁替尼", "category": "BTK抑制剂", "generic_name": "吡托布鲁替尼",
     "contraindications": ["对本品过敏"], "side_effects": ["疲劳", "瘀伤", "感染"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "capivasertib", "name": "卡帕塞替尼", "category": "AKT抑制剂", "generic_name": "卡帕塞替尼",
     "contraindications": ["对本品过敏"], "side_effects": ["皮疹", "腹泻", "高血糖"], "metabolism": "CYP3A4"},
    {"id": "infigratinib", "name": "英菲格拉替尼", "category": "FGFR抑制剂", "generic_name": "英菲格拉替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高磷血症", "视网膜病变"], "metabolism": "CYP3A4"},
    {"id": "futibatinib", "name": "福巴替尼", "category": "FGFR抑制剂", "generic_name": "福巴替尼",
     "contraindications": ["对本品过敏"], "side_effects": ["高磷血症", "甲沟炎"], "metabolism": "CYP3A4"},
    {"id": "erdafitinib", "name": "厄达替尼", "category": "FGFR抑制剂", "generic_name": "厄达替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["高磷血症", "视网膜病变"], "metabolism": "CYP2C9/CYP3A4"},
    {"id": "selpercatinib", "name": "塞普替尼", "category": "RET抑制剂", "generic_name": "塞普替尼",
     "contraindications": ["QT延长"], "side_effects": ["口干", "腹泻", "QT延长"], "metabolism": "CYP3A4"},
    {"id": "pralsetinib", "name": "普拉替尼", "category": "RET抑制剂", "generic_name": "普拉替尼",
     "contraindications": ["对本品过敏"], "side_effects": ["便秘", "疲劳"], "metabolism": "CYP3A4"},
    {"id": "larotrectinib", "name": "拉罗替尼", "category": "TRK抑制剂", "generic_name": "拉罗替尼",
     "contraindications": ["CYP3A4强抑制剂合用"], "side_effects": ["头晕", "疲劳"], "metabolism": "CYP3A4"},
    {"id": "entrectinib", "name": "恩曲替尼", "category": "TRK/ROS1抑制剂", "generic_name": "恩曲替尼",
     "contraindications": ["QT延长"], "side_effects": ["疲劳", "便秘", "QT延长"], "metabolism": "CYP3A4"},
    {"id": "tepotinib", "name": "特泊替尼", "category": "MET抑制剂", "generic_name": "盐酸特泊替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["水肿", "疲劳"], "metabolism": "CYP3A4/CYP2C8"},
    {"id": "capmatinib", "name": "卡马替尼", "category": "MET抑制剂", "generic_name": "盐酸卡马替尼",
     "contraindications": ["严重肝功能不全"], "side_effects": ["水肿", "恶心"], "metabolism": "CYP3A4"},
]

new = [d for d in EXTRAS if d["id"] not in existing_ids]
print(f"Adding {len(new)} new drugs")

# 追加
with open("app/graph/drug_data.py", "r", encoding="utf-8") as f:
    content = f.read()

addition = f"""
# ==================== 第三批扩展(肿瘤靶向) ====================
_EXTRA_DRUGS_3 = {repr(new)}
DRUGS.extend(_EXTRA_DRUGS_3)

"""

marker = "\ndef build_graph_from_data():"
content = content.replace(marker, addition + marker)

with open("app/graph/drug_data.py", "w", encoding="utf-8") as f:
    f.write(content)

importlib.reload(dd)
ids = {d["id"] for d in dd.DRUGS}
print(f"Final: {len(dd.DRUGS)} drugs ({len(ids)} unique), {len(dd.INTERACTIONS)} interactions, {len(dd.ALTERNATIVES)} alternatives")
