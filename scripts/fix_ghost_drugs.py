"""修复10个幽灵药物节点 + 添加交互关系边"""
import json
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "data" / "drug_graph.json"

with open(GRAPH_PATH, encoding="utf-8") as f:
    data = json.load(f)

# ---- 1. 定义10个幽灵药物 ----
ghost_defs = {
    "lithium": {
        "name": "碳酸锂", "category": "情绪稳定剂", "drug": True,
        "generic_name": "碳酸锂",
        "contraindications": ["严重肾功能不全", "严重心脏病", "孕期"],
        "side_effects": ["震颤", "多尿", "甲状腺功能减退", "肾毒性"],
        "metabolism": "肾脏排泄",
    },
    "gemfibrozil": {
        "name": "吉非罗齐", "category": "降脂药", "drug": True,
        "generic_name": "吉非罗齐",
        "contraindications": ["严重肝病", "严重肾功能不全", "胆囊疾病"],
        "side_effects": ["肌痛", "横纹肌溶解", "肝功能异常"],
        "metabolism": "CYP2C8/UGT",
    },
    "tizanidine": {
        "name": "替扎尼定", "category": "肌肉松弛剂", "drug": True,
        "generic_name": "盐酸替扎尼定",
        "contraindications": ["严重肝功能不全", "合用CYP1A2抑制剂"],
        "side_effects": ["嗜睡", "低血压", "肝毒性"],
        "metabolism": "CYP1A2",
    },
    "alcohol": {
        "name": "乙醇", "category": "中枢抑制剂", "drug": True,
        "generic_name": "乙醇",
        "contraindications": ["肝病", "孕期", "合用镇静药"],
        "side_effects": ["中枢抑制", "肝损伤", "依赖性"],
        "metabolism": "ADH/CYP2E1",
    },
    "antacids": {
        "name": "抗酸药", "category": "胃酸中和剂", "drug": True,
        "generic_name": "氢氧化铝/镁",
        "contraindications": ["严重肾功能不全"],
        "side_effects": ["便秘", "腹泻", "电解质紊乱"],
        "metabolism": "不代谢",
    },
    "potassium": {
        "name": "氯化钾", "category": "电解质补充剂", "drug": True,
        "generic_name": "氯化钾",
        "contraindications": ["高钾血症", "严重肾功能不全", "合用保钾利尿剂"],
        "side_effects": ["恶心", "高钾血症", "心律失常"],
        "metabolism": "肾脏排泄",
    },
    "mercaptopurine": {
        "name": "巯嘌呤", "category": "抗肿瘤药", "drug": True,
        "generic_name": "巯嘌呤",
        "contraindications": ["严重肝功能不全", "严重骨髓抑制"],
        "side_effects": ["骨髓抑制", "肝毒性", "恶心"],
        "metabolism": "TPMT/XO",
    },
    "cimetidine": {
        "name": "西咪替丁", "category": "H2受体拮抗剂", "drug": True,
        "generic_name": "西咪替丁",
        "contraindications": ["严重肝肾功能不全"],
        "side_effects": ["头晕", "腹泻", "抗雄激素作用"],
        "metabolism": "CYP1A2/CYP3A4",
    },
    "testosterone": {
        "name": "睾酮", "category": "雄激素", "drug": True,
        "generic_name": "睾酮",
        "contraindications": ["前列腺癌", "乳腺癌", "孕期"],
        "side_effects": ["痤疮", "红细胞增多", "肝毒性"],
        "metabolism": "CYP3A4",
    },
    "hydroxyzine": {
        "name": "羟嗪", "category": "抗组胺药", "drug": True,
        "generic_name": "盐酸羟嗪",
        "contraindications": ["孕期", "QT间期延长"],
        "side_effects": ["嗜睡", "口干", "QT间期延长"],
        "metabolism": "CYP3A4/CYP2D6",
    },
}

updated = 0
for node in data["nodes"]:
    if node["id"] in ghost_defs:
        node["attrs"] = ghost_defs[node["id"]]
        updated += 1
print(f"Updated {updated} ghost nodes")

# ---- 2. 添加交互关系边 ----
new_edges = [
    # lithium
    ("lithium", "ibuprofen", "high", "NSAIDs降低锂排泄,升高血锂浓度"),
    ("lithium", "naproxen", "high", "NSAIDs降低锂排泄"),
    ("lithium", "diclofenac", "high", "NSAIDs降低锂排泄"),
    ("lithium", "lisinopril", "high", "ACE抑制剂降低锂排泄"),
    ("lithium", "losartan", "high", "ARB降低锂排泄"),
    ("lithium", "hydrochlorothiazide", "high", "噻嗪类利尿剂降低锂排泄"),
    ("lithium", "furosemide", "medium", "袢利尿剂可能影响锂排泄"),
    # gemfibrozil
    ("gemfibrozil", "simvastatin", "critical", "CYP2C8抑制,横纹肌溶解风险"),
    ("gemfibrozil", "atorvastatin", "high", "增加他汀类肌毒性"),
    ("gemfibrozil", "rosuvastatin", "high", "增加他汀类肌毒性"),
    # tizanidine
    ("tizanidine", "ciprofloxacin", "critical", "CYP1A2抑制剂,替扎尼定浓度升高"),
    # alcohol
    ("alcohol", "diazepam", "critical", "协同中枢抑制,呼吸抑制风险"),
    ("alcohol", "alprazolam", "critical", "协同中枢抑制"),
    ("alcohol", "tramadol", "critical", "协同中枢抑制"),
    ("alcohol", "acetaminophen", "high", "增加肝毒性"),
    ("alcohol", "warfarin", "high", "增加出血风险"),
    ("alcohol", "metronidazole", "critical", "双硫仑样反应"),
    # antacids
    ("antacids", "levothyroxine", "high", "降低甲状腺素吸收"),
    ("antacids", "ciprofloxacin", "high", "螯合降低吸收"),
    # potassium
    ("potassium", "spironolactone", "critical", "高钾血症风险"),
    ("potassium", "lisinopril", "high", "ACE抑制剂+钾=高钾血症"),
    ("potassium", "losartan", "high", "ARB+钾=高钾血症"),
    # mercaptopurine
    ("mercaptopurine", "allopurinol", "critical", "XO抑制剂,巯嘌呤毒性增加"),
    # cimetidine
    ("cimetidine", "warfarin", "high", "CYP抑制,华法林浓度升高"),
    ("cimetidine", "diazepam", "high", "CYP抑制,苯二氮卓浓度升高"),
    ("cimetidine", "theophylline", "high", "CYP1A2抑制,茶碱浓度升高"),
    ("cimetidine", "carbamazepine", "high", "CYP抑制,卡马西平浓度升高"),
    # testosterone
    ("testosterone", "warfarin", "medium", "增强抗凝效果"),
    # hydroxyzine
    ("hydroxyzine", "diazepam", "high", "协同中枢抑制"),
    ("hydroxyzine", "codeine", "high", "协同中枢抑制"),
]

# Build existing edge set for dedup
existing = set()
for edge in data["edges"]:
    key = tuple(sorted([edge["source"], edge["target"]]))
    existing.add(key)

added = 0
for src, dst, severity, mechanism in new_edges:
    key = tuple(sorted([src, dst]))
    if key not in existing:
        data["edges"].append({"source": src, "target": dst, "attrs": {"relation": "INTERACTS_WITH", "severity": severity, "mechanism": mechanism}})
        data["edges"].append({"source": dst, "target": src, "attrs": {"relation": "INTERACTS_WITH", "severity": severity, "mechanism": mechanism}})
        existing.add(key)
        added += 1

print(f"Added {added} new interaction pairs ({added * 2} edges)")

# ---- 3. 保存 ----
with open(GRAPH_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
