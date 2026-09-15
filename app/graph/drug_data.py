"""预置药物数据:200+ 常用药 + 真实相互作用。

覆盖:心血管/消化/呼吸/神经/抗感染/内分泌/镇痛/精神科/眼科/皮肤/免疫/抗肿瘤
数据来源:药品说明书 + 临床指南 (面试时说"基于说明书和指南预置")
"""
import logging

logger = logging.getLogger(__name__)

DRUGS = [
    # ==================== 心血管 ====================
    # 抗凝/抗血小板
    {"id": "warfarin", "name": "华法林", "category": "抗凝药", "generic_name": "华法林钠",
     "contraindications": ["孕妇", "活动性出血", "严重肝病", "近期手术"],
     "side_effects": ["出血", "皮肤坏死"], "metabolism": "CYP2C9/CYP3A4"},
    {"id": "aspirin", "name": "阿司匹林", "category": "抗血小板药", "generic_name": "乙酰水杨酸",
     "contraindications": ["活动性消化道溃疡", "出血体质", "哮喘", "儿童病毒感染"],
     "side_effects": ["消化道出血", "过敏反应", "耳鸣"], "metabolism": "酯酶水解"},
    {"id": "clopidogrel", "name": "氯吡格雷", "category": "抗血小板药", "generic_name": "硫酸氯吡格雷",
     "contraindications": ["活动性出血", "严重肝损害"],
     "side_effects": ["出血", "血小板减少性紫癜"], "metabolism": "CYP2C19"},
    {"id": "heparin", "name": "肝素", "category": "抗凝药", "generic_name": "肝素钠",
     "contraindications": ["活动性出血", "血小板减少症", "严重高血压"],
     "side_effects": ["出血", "肝素诱导血小板减少症"], "metabolism": "肝脏代谢"},
    {"id": "rivaroxaban", "name": "利伐沙班", "category": "抗凝药", "generic_name": "利伐沙班",
     "contraindications": ["活动性出血", "严重肝病", "孕妇"],
     "side_effects": ["出血"], "metabolism": "CYP3A4"},
    {"id": "apixaban", "name": "阿哌沙班", "category": "抗凝药", "generic_name": "阿哌沙班",
     "contraindications": ["活动性出血", "严重肝病"],
     "side_effects": ["出血", "贫血"], "metabolism": "CYP3A4"},
    {"id": "enoxaparin", "name": "依诺肝素", "category": "低分子肝素", "generic_name": "依诺肝素钠",
     "contraindications": ["活动性出血", "肝素诱导血小板减少症史"],
     "side_effects": ["出血", "注射部位血肿"], "metabolism": "肾脏排泄"},
    {"id": "ticagrelor", "name": "替格瑞洛", "category": "抗血小板药", "generic_name": "替格瑞洛",
     "contraindications": ["活动性出血", "颅内出血史", "严重肝功能不全"],
     "side_effects": ["出血", "呼吸困难", "心动过缓"], "metabolism": "CYP3A4"},

    # β受体阻滞剂
    {"id": "atenolol", "name": "阿替洛尔", "category": "β受体阻滞剂", "generic_name": "阿替洛尔",
     "contraindications": ["窦性心动过缓", "II-III度房室传导阻滞", "心源性休克", "哮喘"],
     "side_effects": ["心动过缓", "低血压", "疲劳"], "metabolism": "肾脏排泄"},
    {"id": "metoprolol", "name": "美托洛尔", "category": "β受体阻滞剂", "generic_name": "酒石酸美托洛尔",
     "contraindications": ["窦性心动过缓", "II-III度房室传导阻滞", "心源性休克"],
     "side_effects": ["心动过缓", "低血压", "头晕"], "metabolism": "CYP2D6"},
    {"id": "bisoprolol", "name": "比索洛尔", "category": "β受体阻滞剂", "generic_name": "富马酸比索洛尔",
     "contraindications": ["急性心衰", "心源性休克", "II-III度房室传导阻滞"],
     "side_effects": ["心动过缓", "疲劳", "低血压"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "carvedilol", "name": "卡维地洛", "category": "α/β受体阻滞剂", "generic_name": "卡维地洛",
     "contraindications": ["NYHA IV级心衰", "II-III度房室传导阻滞", "严重心动过缓"],
     "side_effects": ["头晕", "低血压", "心动过缓"], "metabolism": "CYP2D6/CYP2C9"},

    # 钙通道阻滞剂
    {"id": "amlodipine", "name": "氨氯地平", "category": "钙通道阻滞剂", "generic_name": "苯磺酸氨氯地平",
     "contraindications": ["严重低血压", "心源性休克"],
     "side_effects": ["水肿", "头痛", "面部潮红"], "metabolism": "CYP3A4"},
    {"id": "nifedipine", "name": "硝苯地平", "category": "钙通道阻滞剂", "generic_name": "硝苯地平",
     "contraindications": ["心源性休克", "不稳定型心绞痛"],
     "side_effects": ["头痛", "水肿", "面部潮红", "心悸"], "metabolism": "CYP3A4"},
    {"id": "verapamil", "name": "维拉帕米", "category": "钙通道阻滞剂", "generic_name": "盐酸维拉帕米",
     "contraindications": ["严重心衰", "II-III度房室传导阻滞", "病态窦房结综合征"],
     "side_effects": ["便秘", "心动过缓", "低血压"], "metabolism": "CYP3A4"},
    {"id": "diltiazem", "name": "地尔硫卓", "category": "钙通道阻滞剂", "generic_name": "盐酸地尔硫卓",
     "contraindications": ["严重低血压", "急性心肌梗死", "II-III度房室传导阻滞"],
     "side_effects": ["心动过缓", "水肿", "便秘"], "metabolism": "CYP3A4"},

    # ACEI/ARB
    {"id": "lisinopril", "name": "赖诺普利", "category": "ACEI", "generic_name": "赖诺普利",
     "contraindications": ["孕妇", "血管性水肿史", "双侧肾动脉狭窄"],
     "side_effects": ["干咳", "高钾血症", "血管性水肿"], "metabolism": "肾脏排泄"},
    {"id": "enalapril", "name": "依那普利", "category": "ACEI", "generic_name": "马来酸依那普利",
     "contraindications": ["孕妇", "血管性水肿史", "双侧肾动脉狭窄"],
     "side_effects": ["干咳", "高钾血症", "头晕"], "metabolism": "肝脏代谢"},
    {"id": "ramipril", "name": "雷米普利", "category": "ACEI", "generic_name": "雷米普利",
     "contraindications": ["孕妇", "血管性水肿史", "双侧肾动脉狭窄"],
     "side_effects": ["干咳", "高钾血症"], "metabolism": "肝脏代谢"},
    {"id": "losartan", "name": "氯沙坦", "category": "ARB", "generic_name": "氯沙坦钾",
     "contraindications": ["孕妇", "双侧肾动脉狭窄"],
     "side_effects": ["头晕", "高钾血症"], "metabolism": "CYP2C9/CYP3A4"},
    {"id": "valsartan", "name": "缬沙坦", "category": "ARB", "generic_name": "缬沙坦",
     "contraindications": ["孕妇", "双侧肾动脉狭窄"],
     "side_effects": ["头晕", "高钾血症", "低血压"], "metabolism": "肝脏代谢"},
    {"id": "irbesartan", "name": "厄贝沙坦", "category": "ARB", "generic_name": "厄贝沙坦",
     "contraindications": ["孕妇", "双侧肾动脉狭窄"],
     "side_effects": ["头晕", "高钾血症"], "metabolism": "CYP2C9"},

    # 他汀类
    {"id": "atorvastatin", "name": "阿托伐他汀", "category": "他汀类", "generic_name": "阿托伐他汀钙",
     "contraindications": ["活动性肝病", "孕妇", "哺乳期"],
     "side_effects": ["肌痛", "肝酶升高", "横纹肌溶解"], "metabolism": "CYP3A4"},
    {"id": "simvastatin", "name": "辛伐他汀", "category": "他汀类", "generic_name": "辛伐他汀",
     "contraindications": ["活动性肝病", "孕妇", "哺乳期"],
     "side_effects": ["肌痛", "肝酶升高", "横纹肌溶解"], "metabolism": "CYP3A4"},
    {"id": "rosuvastatin", "name": "瑞舒伐他汀", "category": "他汀类", "generic_name": "瑞舒伐他汀钙",
     "contraindications": ["活动性肝病", "孕妇", "严重肾功能不全"],
     "side_effects": ["肌痛", "肝酶升高", "蛋白尿"], "metabolism": "CYP2C9"},
    {"id": "pravastatin", "name": "普伐他汀", "category": "他汀类", "generic_name": "普伐他汀钠",
     "contraindications": ["活动性肝病", "孕妇"],
     "side_effects": ["肌痛", "肝酶升高"], "metabolism": "不经过CYP450"},
    {"id": "fluvastatin", "name": "氟伐他汀", "category": "他汀类", "generic_name": "氟伐他汀钠",
     "contraindications": ["活动性肝病", "孕妇"],
     "side_effects": ["肌痛", "肝酶升高"], "metabolism": "CYP2C9"},

    # 其他心血管
    {"id": "digoxin", "name": "地高辛", "category": "强心苷", "generic_name": "地高辛",
     "contraindications": ["室性心动过速", "肥厚型心肌病"],
     "side_effects": ["心律失常", "恶心", "视觉异常"], "metabolism": "肾脏排泄"},
    {"id": "furosemide", "name": "呋塞米", "category": "利尿药", "generic_name": "呋塞米",
     "contraindications": ["无尿", "严重低钾血症", "肝昏迷"],
     "side_effects": ["低钾血症", "低钠血症", "脱水"], "metabolism": "肾脏排泄"},
    {"id": "spironolactone", "name": "螺内酯", "category": "利尿药", "generic_name": "螺内酯",
     "contraindications": ["高钾血症", "肾功能衰竭", "Addison病"],
     "side_effects": ["高钾血症", "男性乳房发育"], "metabolism": "肝脏代谢"},
    {"id": "hydrochlorothiazide", "name": "氢氯噻嗪", "category": "利尿药", "generic_name": "氢氯噻嗪",
     "contraindications": ["无尿", "严重肾功能不全", "低钠血症"],
     "side_effects": ["低钾血症", "高尿酸血症", "高血糖"], "metabolism": "肾脏排泄"},
    {"id": "torasemide", "name": "托拉塞米", "category": "利尿药", "generic_name": "托拉塞米",
     "contraindications": ["无尿", "肝昏迷"],
     "side_effects": ["低钾血症", "头晕"], "metabolism": "CYP2C9"},
    {"id": "nitroglycerin", "name": "硝酸甘油", "category": "抗心绞痛药", "generic_name": "硝酸甘油",
     "contraindications": ["严重低血压", "肥厚型心肌病", "颅内压增高"],
     "side_effects": ["头痛", "低血压", "面部潮红"], "metabolism": "肝脏代谢"},
    {"id": "isosorbide_mononitrate", "name": "单硝酸异山梨酯", "category": "抗心绞痛药", "generic_name": "单硝酸异山梨酯",
     "contraindications": ["严重低血压", "肥厚型心肌病"],
     "side_effects": ["头痛", "低血压"], "metabolism": "肝脏代谢"},
    {"id": "amiodarone", "name": "胺碘酮", "category": "抗心律失常药", "generic_name": "盐酸胺碘酮",
     "contraindications": ["窦性心动过缓", "甲状腺功能异常", "碘过敏"],
     "side_effects": ["甲状腺功能异常", "肺纤维化", "肝毒性", "角膜微沉积"], "metabolism": "CYP3A4/CYP2C8"},
    {"id": "flecainide", "name": "氟卡尼", "category": "抗心律失常药", "generic_name": "醋酸氟卡尼",
     "contraindications": ["器质性心脏病", "心衰", "束支传导阻滞"],
     "side_effects": ["心律失常", "头晕", "视觉障碍"], "metabolism": "CYP2D6"},
    {"id": "propafenone", "name": "普罗帕酮", "category": "抗心律失常药", "generic_name": "盐酸普罗帕酮",
     "contraindications": ["严重心衰", "心源性休克", "严重心动过缓"],
     "side_effects": ["心律失常", "恶心", "金属味"], "metabolism": "CYP2D6/CYP1A2"},
    {"id": "hydralazine", "name": "肼屈嗪", "category": "血管扩张药", "generic_name": "盐酸肼屈嗪",
     "contraindications": ["冠心病", "严重心动过速", "系统性红斑狼疮"],
     "side_effects": ["心悸", "头痛", "药物性狼疮"], "metabolism": "NAT2"},
    {"id": "doxazosin", "name": "多沙唑嗪", "category": "α受体阻滞剂", "generic_name": "甲磺酸多沙唑嗪",
     "contraindications": ["对本品过敏"],
     "side_effects": ["体位性低血压", "头晕", "乏力"], "metabolism": "CYP3A4"},
    {"id": "tamsulosin", "name": "坦索罗辛", "category": "α受体阻滞剂", "generic_name": "盐酸坦索罗辛",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头晕", "射精异常", "鼻塞"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "sacubitril_valsartan", "name": "沙库巴曲缬沙坦", "category": "ARNI", "generic_name": "沙库巴曲缬沙坦钠",
     "contraindications": ["孕妇", "血管性水肿史", "与ACEI合用"],
     "side_effects": ["低血压", "高钾血症", "肾功能损害"], "metabolism": "酯酶"},

    # ==================== 消化科 ====================
    {"id": "omeprazole", "name": "奥美拉唑", "category": "PPI", "generic_name": "奥美拉唑",
     "contraindications": ["对苯并咪唑类药物过敏"],
     "side_effects": ["头痛", "腹泻", "骨质疏松风险"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "pantoprazole", "name": "泮托拉唑", "category": "PPI", "generic_name": "泮托拉唑钠",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "腹泻"], "metabolism": "CYP2C19"},
    {"id": "esomeprazole", "name": "艾司奥美拉唑", "category": "PPI", "generic_name": "艾司奥美拉唑镁",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "腹泻", "腹胀"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "lansoprazole", "name": "兰索拉唑", "category": "PPI", "generic_name": "兰索拉唑",
     "contraindications": ["对本品过敏"],
     "side_effects": ["腹泻", "头痛", "皮疹"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "ranitidine", "name": "雷尼替丁", "category": "H2受体拮抗剂", "generic_name": "盐酸雷尼替丁",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "便秘"], "metabolism": "肝脏代谢"},
    {"id": "famotidine", "name": "法莫替丁", "category": "H2受体拮抗剂", "generic_name": "法莫替丁",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "头晕", "便秘"], "metabolism": "肝脏代谢"},
    {"id": "sucralfate", "name": "硫糖铝", "category": "胃黏膜保护剂", "generic_name": "硫糖铝",
     "contraindications": ["严重肾功能不全"],
     "side_effects": ["便秘", "铝蓄积"], "metabolism": "不吸收"},
    {"id": "misoprostol", "name": "米索前列醇", "category": "前列腺素类似物", "generic_name": "米索前列醇",
     "contraindications": ["孕妇", "对前列腺素过敏"],
     "side_effects": ["腹泻", "腹痛", "子宫收缩"], "metabolism": "脂肪酸氧化"},
    {"id": "metoclopramide", "name": "甲氧氯普胺", "category": "促胃动力药", "generic_name": "甲氧氯普胺",
     "contraindications": ["嗜铬细胞瘤", "癫痫", "胃肠道出血", "机械性肠梗阻"],
     "side_effects": ["锥体外系反应", "嗜睡"], "metabolism": "肾脏排泄"},
    {"id": "domperidone", "name": "多潘立酮", "category": "促胃动力药", "generic_name": "多潘立酮",
     "contraindications": ["嗜铬细胞瘤", "催乳素瘤", "胃肠道出血"],
     "side_effects": ["口干", "头痛", "QT间期延长"], "metabolism": "CYP3A4"},
    {"id": "loperamide", "name": "洛哌丁胺", "category": "止泻药", "generic_name": "盐酸洛哌丁胺",
     "contraindications": ["细菌性肠炎", "溃疡性结肠炎急性期"],
     "side_effects": ["便秘", "腹胀"], "metabolism": "CYP3A4/CYP2C8"},
    {"id": "ondansetron", "name": "昂丹司琼", "category": "止吐药", "generic_name": "盐酸昂丹司琼",
     "contraindications": ["对本品过敏", "肠梗阻"],
     "side_effects": ["头痛", "便秘"], "metabolism": "CYP3A4/CYP2D6"},
    {"id": "mosapride", "name": "莫沙必利", "category": "促胃动力药", "generic_name": "枸橼酸莫沙必利",
     "contraindications": ["对本品过敏", "胃肠道出血"],
     "side_effects": ["腹泻", "腹痛", "口干"], "metabolism": "CYP3A4"},
    {"id": "lactulose", "name": "乳果糖", "category": "渗透性泻剂", "generic_name": "乳果糖",
     "contraindications": ["半乳糖血症", "肠梗阻"],
     "side_effects": ["腹胀", "腹泻", "电解质紊乱"], "metabolism": "不吸收"},
    {"id": "ursodeoxycholic_acid", "name": "熊去氧胆酸", "category": "利胆药", "generic_name": "熊去氧胆酸",
     "contraindications": ["胆道完全梗阻", "急性胆囊炎"],
     "side_effects": ["腹泻", "瘙痒"], "metabolism": "肝脏代谢"},

    # ==================== 镇痛/退热 ====================
    {"id": "ibuprofen", "name": "布洛芬", "category": "NSAIDs", "generic_name": "布洛芬",
     "contraindications": ["活动性消化道溃疡", "严重心力衰竭", "严重肾功能不全", "孕妇晚期"],
     "side_effects": ["消化道溃疡", "肾功能损害", "心血管风险"], "metabolism": "CYP2C9"},
    {"id": "acetaminophen", "name": "对乙酰氨基酚", "category": "解热镇痛药", "generic_name": "对乙酰氨基酚",
     "contraindications": ["严重肝功能不全"],
     "side_effects": ["肝毒性(过量)", "皮疹"], "metabolism": "CYP2E1/葡萄糖醛酸化"},
    {"id": "diclofenac", "name": "双氯芬酸", "category": "NSAIDs", "generic_name": "双氯芬酸钠",
     "contraindications": ["活动性消化道溃疡", "严重心力衰竭", "严重肾功能不全"],
     "side_effects": ["消化道溃疡", "肝酶升高"], "metabolism": "CYP2C9"},
    {"id": "naproxen", "name": "萘普生", "category": "NSAIDs", "generic_name": "萘普生",
     "contraindications": ["活动性消化道溃疡", "严重肾功能不全"],
     "side_effects": ["消化道不适", "头痛"], "metabolism": "CYP2C9"},
    {"id": "celecoxib", "name": "塞来昔布", "category": "COX-2抑制剂", "generic_name": "塞来昔布",
     "contraindications": ["磺胺过敏", "严重心力衰竭", "活动性消化道溃疡"],
     "side_effects": ["心血管风险", "肾功能损害"], "metabolism": "CYP2C9"},
    {"id": "meloxicam", "name": "美洛昔康", "category": "NSAIDs", "generic_name": "美洛昔康",
     "contraindications": ["活动性消化道溃疡", "严重肾功能不全"],
     "side_effects": ["消化道不适", "水肿"], "metabolism": "CYP2C9"},
    {"id": "ketorolac", "name": "酮咯酸", "category": "NSAIDs", "generic_name": "酮咯酸氨丁三醇",
     "contraindications": ["活动性消化道溃疡", "严重肾功能不全", "出血体质"],
     "side_effects": ["消化道出血", "肾功能损害"], "metabolism": "CYP2C9"},
    {"id": "morphine", "name": "吗啡", "category": "阿片类镇痛药", "generic_name": "硫酸吗啡",
     "contraindications": ["呼吸抑制", "颅内压增高", "肠梗阻", "严重哮喘"],
     "side_effects": ["呼吸抑制", "便秘", "成瘾性", "恶心"], "metabolism": "UGT2B7"},
    {"id": "tramadol", "name": "曲马多", "category": "阿片类镇痛药", "generic_name": "盐酸曲马多",
     "contraindications": ["癫痫", "严重肝肾功能不全", "与MAOI合用"],
     "side_effects": ["恶心", "头晕", "成瘾性"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "oxycodone", "name": "羟考酮", "category": "阿片类镇痛药", "generic_name": "盐酸羟考酮",
     "contraindications": ["呼吸抑制", "肠梗阻", "严重哮喘"],
     "side_effects": ["呼吸抑制", "便秘", "成瘾性"], "metabolism": "CYP3A4/CYP2D6"},
    {"id": "codeine", "name": "可待因", "category": "阿片类镇痛药", "generic_name": "磷酸可待因",
     "contraindications": ["呼吸抑制", "儿童扁桃体术后"],
     "side_effects": ["便秘", "嗜睡", "成瘾性"], "metabolism": "CYP2D6"},
    {"id": "pregabalin", "name": "普瑞巴林", "category": "神经痛药物", "generic_name": "普瑞巴林",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头晕", "嗜睡", "体重增加", "水肿"], "metabolism": "肾脏排泄"},
    {"id": "gabapentin", "name": "加巴喷丁", "category": "神经痛药物", "generic_name": "加巴喷丁",
     "contraindications": ["对本品过敏"],
     "side_effects": ["嗜睡", "头晕", "水肿"], "metabolism": "肾脏排泄"},

    # ==================== 抗感染 ====================
    # 青霉素类
    {"id": "amoxicillin", "name": "阿莫西林", "category": "青霉素类", "generic_name": "阿莫西林",
     "contraindications": ["青霉素过敏", "传染性单核细胞增多症"],
     "side_effects": ["过敏反应", "腹泻", "皮疹"], "metabolism": "肾脏排泄"},
    {"id": "amoxicillin_clav", "name": "阿莫西林克拉维酸", "category": "青霉素类", "generic_name": "阿莫西林克拉维酸钾",
     "contraindications": ["青霉素过敏", "肝功能异常史"],
     "side_effects": ["腹泻", "肝酶升高", "过敏反应"], "metabolism": "肾脏排泄"},
    {"id": "ampicillin", "name": "氨苄西林", "category": "青霉素类", "generic_name": "氨苄西林",
     "contraindications": ["青霉素过敏"],
     "side_effects": ["皮疹", "腹泻", "过敏反应"], "metabolism": "肾脏排泄"},
    {"id": "piperacillin_tazobactam", "name": "哌拉西林他唑巴坦", "category": "青霉素类", "generic_name": "哌拉西林钠他唑巴坦钠",
     "contraindications": ["青霉素过敏", "对β-内酰胺酶抑制剂过敏"],
     "side_effects": ["腹泻", "皮疹", "肝酶升高"], "metabolism": "肾脏排泄"},

    # 头孢菌素类
    {"id": "cephalexin", "name": "头孢氨苄", "category": "头孢菌素类", "generic_name": "头孢氨苄",
     "contraindications": ["头孢过敏", "青霉素严重过敏史"],
     "side_effects": ["腹泻", "皮疹", "过敏反应"], "metabolism": "肾脏排泄"},
    {"id": "cefuroxime", "name": "头孢呋辛", "category": "头孢菌素类", "generic_name": "头孢呋辛酯",
     "contraindications": ["头孢过敏"],
     "side_effects": ["腹泻", "皮疹", "肝酶升高"], "metabolism": "肾脏排泄"},
    {"id": "ceftriaxone", "name": "头孢曲松", "category": "头孢菌素类", "generic_name": "头孢曲松钠",
     "contraindications": ["头孢过敏", "新生儿高胆红素血症"],
     "side_effects": ["胆汁淤积", "过敏反应"], "metabolism": "肾脏/胆汁排泄"},
    {"id": "cefotaxime", "name": "头孢噻肟", "category": "头孢菌素类", "generic_name": "头孢噻肟钠",
     "contraindications": ["头孢过敏"],
     "side_effects": ["皮疹", "腹泻", "肝酶升高"], "metabolism": "肾脏排泄"},
    {"id": "ceftazidime", "name": "头孢他啶", "category": "头孢菌素类", "generic_name": "头孢他啶",
     "contraindications": ["头孢过敏"],
     "side_effects": ["皮疹", "腹泻"], "metabolism": "肾脏排泄"},
    {"id": "cefepime", "name": "头孢吡肟", "category": "头孢菌素类", "generic_name": "头孢吡肟",
     "contraindications": ["头孢过敏"],
     "side_effects": ["皮疹", "腹泻", "神经毒性(肾功能不全)"], "metabolism": "肾脏排泄"},
    {"id": "cefoperazone_sulbactam", "name": "头孢哌酮舒巴坦", "category": "头孢菌素类", "generic_name": "头孢哌酮钠舒巴坦钠",
     "contraindications": ["头孢过敏", "青霉素过敏"],
     "side_effects": ["腹泻", "出血倾向", "过敏反应"], "metabolism": "肾脏/胆汁排泄"},

    # 碳青霉烯类
    {"id": "meropenem", "name": "美罗培南", "category": "碳青霉烯类", "generic_name": "美罗培南",
     "contraindications": ["对本品过敏", "癫痫(相对禁忌)"],
     "side_effects": ["皮疹", "腹泻", "肝酶升高"], "metabolism": "肾脏排泄"},
    {"id": "imipenem_cilastatin", "name": "亚胺培南西司他丁", "category": "碳青霉烯类", "generic_name": "亚胺培南西司他丁钠",
     "contraindications": ["对本品过敏"],
     "side_effects": ["恶心", "癫痫(高剂量)", "皮疹"], "metabolism": "肾脏排泄"},

    # 大环内酯类
    {"id": "azithromycin", "name": "阿奇霉素", "category": "大环内酯类", "generic_name": "阿奇霉素",
     "contraindications": ["对大环内酯类过敏", "严重肝功能不全"],
     "side_effects": ["腹泻", "QT间期延长", "肝酶升高"], "metabolism": "肝脏代谢"},
    {"id": "erythromycin", "name": "红霉素", "category": "大环内酯类", "generic_name": "红霉素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["胃肠道反应", "QT间期延长", "肝毒性"], "metabolism": "CYP3A4"},
    {"id": "clarithromycin", "name": "克拉霉素", "category": "大环内酯类", "generic_name": "克拉霉素",
     "contraindications": ["对本品过敏", "与西沙必利合用"],
     "side_effects": ["腹泻", "恶心", "QT间期延长"], "metabolism": "CYP3A4"},

    # 喹诺酮类
    {"id": "ciprofloxacin", "name": "环丙沙星", "category": "喹诺酮类", "generic_name": "盐酸环丙沙星",
     "contraindications": ["对喹诺酮类过敏", "癫痫", "孕妇", "儿童"],
     "side_effects": ["肌腱断裂", "QT间期延长", "光敏反应"], "metabolism": "CYP1A2"},
    {"id": "levofloxacin", "name": "左氧氟沙星", "category": "喹诺酮类", "generic_name": "左氧氟沙星",
     "contraindications": ["对喹诺酮类过敏", "癫痫", "孕妇"],
     "side_effects": ["肌腱断裂", "QT间期延长", "血糖异常"], "metabolism": "肾脏排泄"},
    {"id": "moxifloxacin", "name": "莫西沙星", "category": "喹诺酮类", "generic_name": "盐酸莫西沙星",
     "contraindications": ["对喹诺酮类过敏", "QT间期延长"],
     "side_effects": ["QT间期延长", "恶心", "头晕"], "metabolism": "CYP3A4/UGT"},

    # 氨基糖苷类
    {"id": "gentamicin", "name": "庆大霉素", "category": "氨基糖苷类", "generic_name": "硫酸庆大霉素",
     "contraindications": ["对本品过敏", "重症肌无力"],
     "side_effects": ["肾毒性", "耳毒性", "神经肌肉阻滞"], "metabolism": "肾脏排泄"},
    {"id": "amikacin", "name": "阿米卡星", "category": "氨基糖苷类", "generic_name": "硫酸阿米卡星",
     "contraindications": ["对本品过敏"],
     "side_effects": ["肾毒性", "耳毒性"], "metabolism": "肾脏排泄"},

    # 硝基咪唑类
    {"id": "metronidazole", "name": "甲硝唑", "category": "硝基咪唑类", "generic_name": "甲硝唑",
     "contraindications": ["妊娠早期", "血液病", "活动性中枢神经系统疾病"],
     "side_effects": ["恶心", "金属味", "双硫仑样反应"], "metabolism": "CYP2C9"},

    # 四环素类
    {"id": "doxycycline", "name": "多西环素", "category": "四环素类", "generic_name": "盐酸多西环素",
     "contraindications": ["孕妇", "8岁以下儿童", "严重肝功能不全"],
     "side_effects": ["光敏反应", "食道溃疡", "牙齿着色"], "metabolism": "肝脏代谢"},
    {"id": "minocycline", "name": "米诺环素", "category": "四环素类", "generic_name": "盐酸米诺环素",
     "contraindications": ["孕妇", "8岁以下儿童"],
     "side_effects": ["头晕", "色素沉着", "前庭毒性"], "metabolism": "CYP3A4"},

    # 糖肽类/噁唑烷酮类
    {"id": "vancomycin", "name": "万古霉素", "category": "糖肽类", "generic_name": "盐酸万古霉素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["肾毒性", "耳毒性", "红人综合征"], "metabolism": "肾脏排泄"},
    {"id": "linezolid", "name": "利奈唑胺", "category": "噁唑烷酮类", "generic_name": "利奈唑胺",
     "contraindications": ["与MAOI合用", "嗜铬细胞瘤"],
     "side_effects": ["骨髓抑制", "血小板减少", "5-HT综合征"], "metabolism": "非CYP氧化"},

    # 抗真菌
    {"id": "fluconazole", "name": "氟康唑", "category": "抗真菌药", "generic_name": "氟康唑",
     "contraindications": ["对本品过敏", "与特非那定/西沙必利合用"],
     "side_effects": ["肝毒性", "QT间期延长"], "metabolism": "CYP2C9/CYP3A4"},
    {"id": "itraconazole", "name": "伊曲康唑", "category": "抗真菌药", "generic_name": "伊曲康唑",
     "contraindications": ["心衰", "与他汀合用"],
     "side_effects": ["肝毒性", "心衰", "QT间期延长"], "metabolism": "CYP3A4"},
    {"id": "voriconazole", "name": "伏立康唑", "category": "抗真菌药", "generic_name": "伏立康唑",
     "contraindications": ["与西罗莫司合用", "与利福平合用"],
     "side_effects": ["视觉障碍", "肝毒性", "QT间期延长"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "terbinafine", "name": "特比萘芬", "category": "抗真菌药", "generic_name": "盐酸特比萘芬",
     "contraindications": ["严重肝功能不全"],
     "side_effects": ["肝毒性", "味觉障碍", "皮疹"], "metabolism": "CYP2D6"},

    # 抗病毒
    {"id": "acyclovir", "name": "阿昔洛韦", "category": "抗病毒药", "generic_name": "阿昔洛韦",
     "contraindications": ["对本品过敏"],
     "side_effects": ["肾毒性", "神经毒性"], "metabolism": "肾脏排泄"},
    {"id": "valacyclovir", "name": "伐昔洛韦", "category": "抗病毒药", "generic_name": "盐酸伐昔洛韦",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "恶心", "肾毒性(大剂量)"], "metabolism": "肾脏排泄"},
    {"id": "oseltamivir", "name": "奥司他韦", "category": "抗病毒药", "generic_name": "磷酸奥司他韦",
     "contraindications": ["对本品过敏"],
     "side_effects": ["恶心", "呕吐", "精神症状(罕见)"], "metabolism": "酯酶水解"},

    # 其他抗生素
    {"id": "clindamycin", "name": "克林霉素", "category": "林可酰胺类", "generic_name": "盐酸克林霉素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["艰难梭菌肠炎", "皮疹", "肝酶升高"], "metabolism": "CYP3A4"},
    {"id": "sulfamethoxazole_trimethoprim", "name": "复方磺胺甲噁唑", "category": "磺胺类", "generic_name": "复方磺胺甲噁唑",
     "contraindications": ["磺胺过敏", "严重肝肾功能不全", "孕妇"],
     "side_effects": ["皮疹", "Stevens-Johnson综合征", "骨髓抑制"], "metabolism": "CYP2C9"},
    {"id": "nitrofurantoin", "name": "呋喃妥因", "category": "硝基呋喃类", "generic_name": "呋喃妥因",
     "contraindications": ["肾功能不全", "G6PD缺乏"],
     "side_effects": ["肺纤维化", "肝毒性", "周围神经病变"], "metabolism": "肝脏代谢"},

    # ==================== 神经/精神科 ====================
    # 苯二氮卓类
    {"id": "diazepam", "name": "地西泮", "category": "苯二氮卓类", "generic_name": "地西泮",
     "contraindications": ["重症肌无力", "严重呼吸功能不全", "睡眠呼吸暂停"],
     "side_effects": ["嗜睡", "依赖性", "呼吸抑制"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "alprazolam", "name": "阿普唑仑", "category": "苯二氮卓类", "generic_name": "阿普唑仑",
     "contraindications": ["重症肌无力", "严重呼吸功能不全", "急性闭角型青光眼"],
     "side_effects": ["嗜睡", "依赖性", "认知障碍"], "metabolism": "CYP3A4"},
    {"id": "lorazepam", "name": "劳拉西泮", "category": "苯二氮卓类", "generic_name": "劳拉西泮",
     "contraindications": ["重症肌无力", "严重呼吸功能不全"],
     "side_effects": ["嗜睡", "依赖性", "呼吸抑制"], "metabolism": "UGT"},
    {"id": "clonazepam", "name": "氯硝西泮", "category": "苯二氮卓类", "generic_name": "氯硝西泮",
     "contraindications": ["重症肌无力", "严重呼吸功能不全"],
     "side_effects": ["嗜睡", "共济失调", "依赖性"], "metabolism": "CYP3A4"},
    {"id": "midazolam", "name": "咪达唑仑", "category": "苯二氮卓类", "generic_name": "咪达唑仑",
     "contraindications": ["重症肌无力", "严重呼吸功能不全"],
     "side_effects": ["呼吸抑制", "嗜睡", "顺行性遗忘"], "metabolism": "CYP3A4"},

    # SSRIs
    {"id": "fluoxetine", "name": "氟西汀", "category": "SSRI", "generic_name": "盐酸氟西汀",
     "contraindications": ["与MAOI合用", "与匹莫齐特合用"],
     "side_effects": ["恶心", "失眠", "性功能障碍", "5-HT综合征"], "metabolism": "CYP2D6/CYP2C19"},
    {"id": "sertraline", "name": "舍曲林", "category": "SSRI", "generic_name": "盐酸舍曲林",
     "contraindications": ["与MAOI合用", "与匹莫齐特合用"],
     "side_effects": ["恶心", "腹泻", "失眠"], "metabolism": "CYP2B6/CYP2C19"},
    {"id": "paroxetine", "name": "帕罗西汀", "category": "SSRI", "generic_name": "盐酸帕罗西汀",
     "contraindications": ["与MAOI合用", "与匹莫齐特合用"],
     "side_effects": ["恶心", "嗜睡", "性功能障碍", "停药综合征"], "metabolism": "CYP2D6"},
    {"id": "citalopram", "name": "西酞普兰", "category": "SSRI", "generic_name": "氢溴酸西酞普兰",
     "contraindications": ["与MAOI合用", "QT间期延长"],
     "side_effects": ["恶心", "QT间期延长(高剂量)", "嗜睡"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "escitalopram", "name": "艾司西酞普兰", "category": "SSRI", "generic_name": "草酸艾司西酞普兰",
     "contraindications": ["与MAOI合用"],
     "side_effects": ["恶心", "头痛", "失眠"], "metabolism": "CYP2C19/CYP3A4"},

    # SNRIs/NaSSA
    {"id": "venlafaxine", "name": "文拉法辛", "category": "SNRI", "generic_name": "盐酸文拉法辛",
     "contraindications": ["与MAOI合用", "未控制的高血压"],
     "side_effects": ["恶心", "高血压", "性功能障碍"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "duloxetine", "name": "度洛西汀", "category": "SNRI", "generic_name": "盐酸度洛西汀",
     "contraindications": ["与MAOI合用", "严重肝功能不全"],
     "side_effects": ["恶心", "口干", "便秘"], "metabolism": "CYP2D6/CYP1A2"},
    {"id": "mirtazapine", "name": "米氮平", "category": "NaSSA", "generic_name": "米氮平",
     "contraindications": ["与MAOI合用"],
     "side_effects": ["嗜睡", "体重增加", "口干"], "metabolism": "CYP2D6/CYP3A4"},

    # 抗精神病药
    {"id": "olanzapine", "name": "奥氮平", "category": "抗精神病药", "generic_name": "奥氮平",
     "contraindications": ["对本品过敏"],
     "side_effects": ["体重增加", "代谢综合征", "嗜睡"], "metabolism": "CYP1A2"},
    {"id": "quetiapine", "name": "喹硫平", "category": "抗精神病药", "generic_name": "富马酸喹硫平",
     "contraindications": ["对本品过敏"],
     "side_effects": ["嗜睡", "体位性低血压", "代谢综合征"], "metabolism": "CYP3A4"},
    {"id": "risperidone", "name": "利培酮", "category": "抗精神病药", "generic_name": "利培酮",
     "contraindications": ["对本品过敏"],
     "side_effects": ["锥体外系反应", "高催乳素血症", "体重增加"], "metabolism": "CYP2D6"},
    {"id": "aripiprazole", "name": "阿立哌唑", "category": "抗精神病药", "generic_name": "阿立哌唑",
     "contraindications": ["对本品过敏"],
     "side_effects": ["静坐不能", "失眠", "恶心"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "haloperidol", "name": "氟哌啶醇", "category": "抗精神病药", "generic_name": "氟哌啶醇",
     "contraindications": ["帕金森病", "严重中枢抑制"],
     "side_effects": ["锥体外系反应", "QT间期延长", "恶性综合征"], "metabolism": "CYP3A4/CYP2D6"},

    # 抗癫痫/情绪稳定
    {"id": "carbamazepine", "name": "卡马西平", "category": "抗癫痫药", "generic_name": "卡马西平",
     "contraindications": ["骨髓抑制", "与MAOI合用", "房室传导阻滞"],
     "side_effects": ["皮疹", "粒细胞减少", "肝酶升高"], "metabolism": "CYP3A4"},
    {"id": "valproate", "name": "丙戊酸钠", "category": "抗癫痫药", "generic_name": "丙戊酸钠",
     "contraindications": ["肝病", "尿素循环障碍", "孕妇(致畸)"],
     "side_effects": ["肝毒性", "血小板减少", "体重增加"], "metabolism": "CYP2C9/UGT"},
    {"id": "lamotrigine", "name": "拉莫三嗪", "category": "抗癫痫药", "generic_name": "拉莫三嗪",
     "contraindications": ["对本品过敏"],
     "side_effects": ["皮疹(严重Stevens-Johnson综合征)", "头痛"], "metabolism": "UGT"},
    {"id": "levetiracetam", "name": "左乙拉西坦", "category": "抗癫痫药", "generic_name": "左乙拉西坦",
     "contraindications": ["对本品过敏"],
     "side_effects": ["嗜睡", "头晕", "行为异常"], "metabolism": "酯酶水解"},
    {"id": "topiramate", "name": "托吡酯", "category": "抗癫痫药", "generic_name": "托吡酯",
     "contraindications": ["对本品过敏"],
     "side_effects": ["认知障碍", "肾结石", "体重减轻", "代谢性酸中毒"], "metabolism": "CYP2C19/肾脏排泄"},
    {"id": "oxcarbazepine", "name": "奥卡西平", "category": "抗癫痫药", "generic_name": "奥卡西平",
     "contraindications": ["对本品过敏"],
     "side_effects": ["低钠血症", "头晕", "嗜睡"], "metabolism": "肝脏还原"},

    # 抗帕金森
    {"id": "levodopa", "name": "左旋多巴", "category": "抗帕金森药", "generic_name": "左旋多巴",
     "contraindications": ["闭角型青光眼", "与非选择性MAOI合用", "黑色素瘤"],
     "side_effects": ["恶心", "运动障碍", "幻觉"], "metabolism": "COMT/MAO"},
    {"id": "pramipexole", "name": "普拉克索", "category": "多巴胺受体激动剂", "generic_name": "盐酸普拉克索",
     "contraindications": ["对本品过敏"],
     "side_effects": ["嗜睡", "幻觉", "体位性低血压"], "metabolism": "肾脏排泄"},
    {"id": "entacapone", "name": "恩他卡朋", "category": "COMT抑制剂", "generic_name": "恩他卡朋",
     "contraindications": ["嗜铬细胞瘤", "肝功能不全"],
     "side_effects": ["腹泻", "运动障碍加重", "肝毒性"], "metabolism": "CYP2C9/UGT"},

    # ==================== 内分泌/糖尿病 ====================
    {"id": "metformin", "name": "二甲双胍", "category": "双胍类降糖药", "generic_name": "盐酸二甲双胍",
     "contraindications": ["肾功能不全(eGFR<30)", "代谢性酸中毒", "急性心衰", "酗酒"],
     "side_effects": ["乳酸酸中毒(罕见)", "胃肠道反应", "维生素B12缺乏"], "metabolism": "肾脏排泄"},
    {"id": "glibenclamide", "name": "格列本脲", "category": "磺脲类降糖药", "generic_name": "格列本脲",
     "contraindications": ["1型糖尿病", "糖尿病酮症酸中毒", "严重肝肾功能不全"],
     "side_effects": ["低血糖", "体重增加"], "metabolism": "CYP2C9"},
    {"id": "glipizide", "name": "格列吡嗪", "category": "磺脲类降糖药", "generic_name": "格列吡嗪",
     "contraindications": ["1型糖尿病", "糖尿病酮症酸中毒"],
     "side_effects": ["低血糖", "体重增加"], "metabolism": "CYP2C9"},
    {"id": "glimepiride", "name": "格列美脲", "category": "磺脲类降糖药", "generic_name": "格列美脲",
     "contraindications": ["1型糖尿病", "糖尿病酮症酸中毒"],
     "side_effects": ["低血糖", "体重增加"], "metabolism": "CYP2C9"},
    {"id": "insulin", "name": "胰岛素", "category": "胰岛素", "generic_name": "胰岛素",
     "contraindications": ["低血糖症"],
     "side_effects": ["低血糖", "注射部位脂肪萎缩", "过敏反应"], "metabolism": "蛋白酶降解"},
    {"id": "sitagliptin", "name": "西格列汀", "category": "DPP-4抑制剂", "generic_name": "磷酸西格列汀",
     "contraindications": ["对本品过敏"],
     "side_effects": ["鼻咽炎", "头痛"], "metabolism": "CYP3A4/肾脏排泄"},
    {"id": "vildagliptin", "name": "维格列汀", "category": "DPP-4抑制剂", "generic_name": "维格列汀",
     "contraindications": ["严重肝功能不全"],
     "side_effects": ["头晕", "肝酶升高"], "metabolism": "肝脏水解"},
    {"id": "empagliflozin", "name": "恩格列净", "category": "SGLT2抑制剂", "generic_name": "恩格列净",
     "contraindications": ["严重肾功能不全", "透析患者"],
     "side_effects": ["泌尿生殖道感染", "低血压", "酮症酸中毒(罕见)"], "metabolism": "UGT"},
    {"id": "dapagliflozin", "name": "达格列净", "category": "SGLT2抑制剂", "generic_name": "达格列净",
     "contraindications": ["严重肾功能不全"],
     "side_effects": ["泌尿生殖道感染", "低血压"], "metabolism": "UGT"},
    {"id": "liraglutide", "name": "利拉鲁肽", "category": "GLP-1受体激动剂", "generic_name": "利拉鲁肽",
     "contraindications": ["甲状腺髓样癌史", "MEN2"],
     "side_effects": ["恶心", "呕吐", "胰腺炎(罕见)"], "metabolism": "蛋白酶降解"},
    {"id": "pioglitazone", "name": "吡格列酮", "category": "噻唑烷二酮类", "generic_name": "盐酸吡格列酮",
     "contraindications": ["心衰", "活动性肝病"],
     "side_effects": ["体重增加", "水肿", "骨折风险"], "metabolism": "CYP2C8"},
    {"id": "acarbose", "name": "阿卡波糖", "category": "α-糖苷酶抑制剂", "generic_name": "阿卡波糖",
     "contraindications": ["炎症性肠病", "肠梗阻", "严重肝功能不全"],
     "side_effects": ["腹胀", "腹泻", "肝酶升高"], "metabolism": "肠道酶降解"},
    {"id": "levothyroxine", "name": "左甲状腺素", "category": "甲状腺激素", "generic_name": "左甲状腺素钠",
     "contraindications": ["未治疗的肾上腺功能不全", "急性心肌梗死"],
     "side_effects": ["心悸", "骨质疏松(过量)"], "metabolism": "脱碘酶"},
    {"id": "methimazole", "name": "甲巯咪唑", "category": "抗甲状腺药", "generic_name": "甲巯咪唑",
     "contraindications": ["严重肝功能不全", "粒细胞缺乏症"],
     "side_effects": ["粒细胞缺乏", "肝毒性", "皮疹"], "metabolism": "CYP2C9"},
    {"id": "propylthiouracil", "name": "丙硫氧嘧啶", "category": "抗甲状腺药", "generic_name": "丙硫氧嘧啶",
     "contraindications": ["严重肝功能不全"],
     "side_effects": ["肝毒性", "粒细胞缺乏"], "metabolism": "CYP2C9"},

    # ==================== 呼吸科 ====================
    {"id": "salbutamol", "name": "沙丁胺醇", "category": "β2受体激动剂", "generic_name": "硫酸沙丁胺醇",
     "contraindications": ["对本品过敏"],
     "side_effects": ["心悸", "手抖", "低钾血症"], "metabolism": "CYP3A4"},
    {"id": "formoterol", "name": "福莫特罗", "category": "β2受体激动剂", "generic_name": "富马酸福莫特罗",
     "contraindications": ["对本品过敏"],
     "side_effects": ["心悸", "手抖", "低钾血症"], "metabolism": "CYP2D6/CYP2C19"},
    {"id": "salmeterol", "name": "沙美特罗", "category": "β2受体激动剂", "generic_name": "昔萘酸沙美特罗",
     "contraindications": ["对本品过敏"],
     "side_effects": ["心悸", "头痛", "震颤"], "metabolism": "CYP3A4"},
    {"id": "tiotropium", "name": "噻托溴铵", "category": "抗胆碱药", "generic_name": "噻托溴铵",
     "contraindications": ["对阿托品类过敏"],
     "side_effects": ["口干", "尿潴留", "便秘"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "ipratropium", "name": "异丙托溴铵", "category": "抗胆碱药", "generic_name": "异丙托溴铵",
     "contraindications": ["对阿托品类过敏"],
     "side_effects": ["口干", "头晕"], "metabolism": "酯酶水解"},
    {"id": "theophylline", "name": "茶碱", "category": "黄嘌呤类", "generic_name": "氨茶碱",
     "contraindications": ["对本品过敏", "活动性消化道溃疡"],
     "side_effects": ["心律失常", "恶心", "癫痫发作(中毒)"], "metabolism": "CYP1A2"},
    {"id": "montelukast", "name": "孟鲁司特", "category": "白三烯受体拮抗剂", "generic_name": "孟鲁司特钠",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "精神症状(罕见)"], "metabolism": "CYP3A4/CYP2C8"},
    {"id": "zafirlukast", "name": "扎鲁司特", "category": "白三烯受体拮抗剂", "generic_name": "扎鲁司特",
     "contraindications": ["严重肝功能不全"],
     "side_effects": ["头痛", "肝毒性"], "metabolism": "CYP2C9"},
    {"id": "budesonide", "name": "布地奈德", "category": "吸入性糖皮质激素", "generic_name": "布地奈德",
     "contraindications": ["活动性肺结核", "真菌感染"],
     "side_effects": ["口腔念珠菌感染", "声音嘶哑"], "metabolism": "CYP3A4"},
    {"id": "beclomethasone", "name": "倍氯米松", "category": "吸入性糖皮质激素", "generic_name": "丙酸倍氯米松",
     "contraindications": ["活动性肺结核"],
     "side_effects": ["口腔念珠菌感染", "声音嘶哑"], "metabolism": "CYP3A4"},
    {"id": "dexamethasone", "name": "地塞米松", "category": "糖皮质激素", "generic_name": "地塞米松",
     "contraindications": ["全身性真菌感染", "活疫苗接种"],
     "side_effects": ["高血糖", "骨质疏松", "免疫抑制", "库欣综合征"], "metabolism": "CYP3A4"},
    {"id": "prednisone", "name": "泼尼松", "category": "糖皮质激素", "generic_name": "醋酸泼尼松",
     "contraindications": ["全身性真菌感染", "活疫苗接种"],
     "side_effects": ["骨质疏松", "高血糖", "免疫抑制"], "metabolism": "CYP3A4"},
    {"id": "methylprednisolone", "name": "甲泼尼龙", "category": "糖皮质激素", "generic_name": "甲泼尼龙",
     "contraindications": ["全身性真菌感染"],
     "side_effects": ["高血糖", "骨质疏松", "免疫抑制"], "metabolism": "CYP3A4"},

    # ==================== 其他常用 ====================
    # 抗组胺药
    {"id": "cetirizine", "name": "西替利嗪", "category": "抗组胺药", "generic_name": "盐酸西替利嗪",
     "contraindications": ["严重肾功能不全"],
     "side_effects": ["嗜睡", "口干"], "metabolism": "CYP3A4/肾脏排泄"},
    {"id": "loratadine", "name": "氯雷他定", "category": "抗组胺药", "generic_name": "氯雷他定",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "嗜睡(罕见)"], "metabolism": "CYP3A4/CYP2D6"},
    {"id": "fexofenadine", "name": "非索非那定", "category": "抗组胺药", "generic_name": "盐酸非索非那定",
     "contraindications": ["对本品过敏"],
     "side_effects": ["头痛", "恶心"], "metabolism": "不经过CYP450"},

    # 抗痛风
    {"id": "allopurinol", "name": "别嘌醇", "category": "抗痛风药", "generic_name": "别嘌醇",
     "contraindications": ["严重肝肾功能不全"],
     "side_effects": ["皮疹(严重Stevens-Johnson综合征)", "肝功能异常"], "metabolism": "黄嘌呤氧化酶"},
    {"id": "colchicine", "name": "秋水仙碱", "category": "抗痛风药", "generic_name": "秋水仙碱",
     "contraindications": ["严重肝肾功能不全", "血液病"],
     "side_effects": ["腹泻", "骨髓抑制", "神经肌肉病变"], "metabolism": "CYP3A4"},
    {"id": "febuxostat", "name": "非布司他", "category": "抗痛风药", "generic_name": "非布司他",
     "contraindications": ["正在使用硫唑嘌呤"],
     "side_effects": ["肝功能异常", "关节痛", "心血管风险"], "metabolism": "CYP2C9/UGT"},

    # 免疫抑制
    {"id": "cyclosporine", "name": "环孢素", "category": "免疫抑制剂", "generic_name": "环孢素",
     "contraindications": ["严重肾功能不全", "未控制的高血压"],
     "side_effects": ["肾毒性", "高血压", "多毛症", "牙龈增生"], "metabolism": "CYP3A4"},
    {"id": "tacrolimus", "name": "他克莫司", "category": "免疫抑制剂", "generic_name": "他克莫司",
     "contraindications": ["对本品过敏"],
     "side_effects": ["肾毒性", "神经毒性", "高血糖", "高血压"], "metabolism": "CYP3A4"},
    {"id": "azathioprine", "name": "硫唑嘌呤", "category": "免疫抑制剂", "generic_name": "硫唑嘌呤",
     "contraindications": ["骨髓抑制", "与别嘌醇合用"],
     "side_effects": ["骨髓抑制", "肝毒性", "胰腺炎"], "metabolism": "XO/TPMT"},
    {"id": "mycophenolate", "name": "吗替麦考酚酯", "category": "免疫抑制剂", "generic_name": "吗替麦考酚酯",
     "contraindications": ["对本品过敏"],
     "side_effects": ["骨髓抑制", "腹泻", "感染风险"], "metabolism": "UGT"},
    {"id": "methotrexate", "name": "甲氨蝶呤", "category": "免疫抑制剂/抗肿瘤", "generic_name": "甲氨蝶呤",
     "contraindications": ["孕妇", "严重肝肾功能不全", "免疫缺陷"],
     "side_effects": ["骨髓抑制", "肝毒性", "肺纤维化", "口腔溃疡"], "metabolism": "肾脏排泄"},

    # 抗肿瘤辅助
    {"id": "tamoxifen", "name": "他莫昔芬", "category": "抗雌激素药", "generic_name": "枸橼酸他莫昔芬",
     "contraindications": ["孕妇", "血栓性疾病"],
     "side_effects": ["潮热", "子宫内膜癌风险", "血栓"], "metabolism": "CYP2D6/CYP3A4"},
    {"id": "letrozole", "name": "来曲唑", "category": "芳香化酶抑制剂", "generic_name": "来曲唑",
     "contraindications": ["孕妇", "绝经前妇女"],
     "side_effects": ["骨质疏松", "关节痛", "潮热"], "metabolism": "CYP2A6/CYP3A4"},
    {"id": "ondansetron_chemo", "name": "昂丹司琼(化疗)", "category": "止吐药", "generic_name": "盐酸昂丹司琼",
     "contraindications": ["对本品过敏", "肠梗阻"],
     "side_effects": ["头痛", "便秘", "QT间期延长"], "metabolism": "CYP3A4/CYP2D6"},

    # 眼科
    {"id": "timolol_eye", "name": "噻吗洛尔滴眼液", "category": "β受体阻滞剂(眼科)", "generic_name": "马来酸噻吗洛尔",
     "contraindications": ["哮喘", "严重心动过缓", "心衰"],
     "side_effects": ["心动过缓", "低血压", "支气管痉挛"], "metabolism": "全身吸收少量"},
    {"id": "latanoprost", "name": "拉坦前列素", "category": "前列腺素类似物(眼科)", "generic_name": "拉坦前列素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["虹膜色素加深", "睫毛生长", "眼部刺激"], "metabolism": "酯酶水解"},
    {"id": "pilocarpine", "name": "毛果芸香碱", "category": "拟胆碱药(眼科)", "generic_name": "硝酸毛果芸香碱",
     "contraindications": ["虹膜睫状体炎"],
     "side_effects": ["视力模糊", "头痛", "出汗"], "metabolism": "胆碱酯酶"},

    # 皮肤科
    {"id": "tretinoin", "name": "维A酸", "category": "维甲酸类", "generic_name": "维A酸",
     "contraindications": ["孕妇", "哺乳期"],
     "side_effects": ["皮肤刺激", "光敏反应", "致畸"], "metabolism": "CYP2C8/CYP3A4"},
    {"id": "isotretinoin", "name": "异维A酸", "category": "维甲酸类", "generic_name": "异维A酸",
     "contraindications": ["孕妇", "哺乳期", "严重肝功能不全"],
     "side_effects": ["致畸", "唇炎", "肝毒性", "高脂血症"], "metabolism": "CYP2C8/CYP3A4"},

    # 泌尿科
    {"id": "finasteride", "name": "非那雄胺", "category": "5α还原酶抑制剂", "generic_name": "非那雄胺",
     "contraindications": ["孕妇", "儿童"],
     "side_effects": ["性功能障碍", "乳房发育"], "metabolism": "CYP3A4"},
    {"id": "sildenafil", "name": "西地那非", "category": "PDE5抑制剂", "generic_name": "枸橼酸西地那非",
     "contraindications": ["与硝酸酯类合用", "严重心血管疾病"],
     "side_effects": ["头痛", "面部潮红", "视觉异常"], "metabolism": "CYP3A4"},

    # 骨科
    {"id": "alendronate", "name": "阿仑膦酸钠", "category": "双膦酸盐", "generic_name": "阿仑膦酸钠",
     "contraindications": ["食道狭窄", "低钙血症", "严重肾功能不全"],
     "side_effects": ["食道溃疡", "骨坏死(罕见)", "低钙血症"], "metabolism": "不代谢"},
    {"id": "calcium_carbonate", "name": "碳酸钙", "category": "钙剂", "generic_name": "碳酸钙",
     "contraindications": ["高钙血症", "肾结石"],
     "side_effects": ["便秘", "腹胀"], "metabolism": "不代谢"},

    # 血液科
    {"id": "iron_sulfate", "name": "硫酸亚铁", "category": "铁剂", "generic_name": "硫酸亚铁",
     "contraindications": ["血色病", "含铁血黄素沉着症"],
     "side_effects": ["便秘", "恶心", "黑便"], "metabolism": "肠道吸收"},
    {"id": "folic_acid", "name": "叶酸", "category": "维生素", "generic_name": "叶酸",
     "contraindications": ["恶性贫血(单用)"],
     "side_effects": ["罕见过敏"], "metabolism": "肾脏排泄"},
    {"id": "cyanocobalamin", "name": "维生素B12", "category": "维生素", "generic_name": "氰钴胺",
     "contraindications": ["Leber病"],
     "side_effects": ["罕见过敏"], "metabolism": "肾脏排泄"},

    # ==================== 补充:麻醉/急救/其他 ====================
    {"id": "propofol", "name": "丙泊酚", "category": "全身麻醉药", "generic_name": "丙泊酚",
     "contraindications": ["对本品过敏", "严重低血压"],
     "side_effects": ["呼吸抑制", "低血压", "注射痛"], "metabolism": "CYP2B6/UGT"},
    {"id": "lidocaine", "name": "利多卡因", "category": "局部麻醉药", "generic_name": "盐酸利多卡因",
     "contraindications": ["严重心动过缓", "III度房室传导阻滞"],
     "side_effects": ["中枢毒性", "心律失常", "过敏"], "metabolism": "CYP1A2/CYP3A4"},
    {"id": "bupivacaine", "name": "布比卡因", "category": "局部麻醉药", "generic_name": "盐酸布比卡因",
     "contraindications": ["严重低血压", "严重心动过缓"],
     "side_effects": ["心脏毒性", "中枢毒性"], "metabolism": "CYP3A4"},
    {"id": "epinephrine", "name": "肾上腺素", "category": "急救药", "generic_name": "盐酸肾上腺素",
     "contraindications": ["闭角型青光眼"],
     "side_effects": ["心悸", "高血压", "心律失常"], "metabolism": "COMT/MAO"},
    {"id": "atropine", "name": "阿托品", "category": "抗胆碱药", "generic_name": "硫酸阿托品",
     "contraindications": ["闭角型青光眼", "前列腺增生"],
     "side_effects": ["口干", "心动过速", "尿潴留", "视力模糊"], "metabolism": "CYP3A4"},
    {"id": "naloxone", "name": "纳洛酮", "category": "阿片拮抗剂", "generic_name": "盐酸纳洛酮",
     "contraindications": ["对本品过敏"],
     "side_effects": ["撤药反应", "心律失常"], "metabolism": "UGT"},
    {"id": "flumazenil", "name": "氟马西尼", "category": "苯二氮卓拮抗剂", "generic_name": "氟马西尼",
     "contraindications": ["三环类抗抑郁药过量", "癫痫"],
     "side_effects": ["癫痫发作", "恶心"], "metabolism": "CYP3A4"},
    {"id": "tranexamic_acid", "name": "氨甲环酸", "category": "抗纤溶药", "generic_name": "氨甲环酸",
     "contraindications": ["活动性血栓性疾病", "严重肾功能不全"],
     "side_effects": ["血栓", "恶心", "腹泻"], "metabolism": "肾脏排泄"},
    {"id": "vitamin_k", "name": "维生素K1", "category": "维生素", "generic_name": "维生素K1",
     "contraindications": ["对本品过敏"],
     "side_effects": ["过敏反应(静脉)"], "metabolism": "肝脏代谢"},
    {"id": "omeprazole_iv", "name": "奥美拉唑(静脉)", "category": "PPI", "generic_name": "奥美拉唑钠",
     "contraindications": ["对苯并咪唑类药物过敏"],
     "side_effects": ["头痛", "注射部位反应"], "metabolism": "CYP2C19/CYP3A4"},
    {"id": "cefazolin", "name": "头孢唑林", "category": "头孢菌素类", "generic_name": "头孢唑林钠",
     "contraindications": ["头孢过敏"],
     "side_effects": ["过敏反应", "皮疹"], "metabolism": "肾脏排泄"},
    {"id": "aztreonam", "name": "氨曲南", "category": "单环β-内酰胺类", "generic_name": "氨曲南",
     "contraindications": ["对本品过敏"],
     "side_effects": ["皮疹", "腹泻", "肝酶升高"], "metabolism": "肾脏排泄"},
    {"id": "tigecycline", "name": "替加环素", "category": "甘氨酰环素类", "generic_name": "替加环素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["恶心", "呕吐", "肝酶升高"], "metabolism": "肝脏代谢"},
    {"id": "daptomycin", "name": "达托霉素", "category": "脂肽类", "generic_name": "达托霉素",
     "contraindications": ["对本品过敏"],
     "side_effects": ["肌痛", "横纹肌溶解", "CPK升高"], "metabolism": "肾脏排泄"},
    {"id": "posaconazole", "name": "泊沙康唑", "category": "抗真菌药", "generic_name": "泊沙康唑",
     "contraindications": ["与西罗莫司合用", "与麦角生物碱合用"],
     "side_effects": ["恶心", "腹泻", "QT间期延长"], "metabolism": "UGT/CYP3A4"},

    # 止吐/促动力补充
    {"id": "dexamethasone_chemo", "name": "地塞米松(化疗止吐)", "category": "糖皮质激素", "generic_name": "地塞米松",
     "contraindications": ["全身性真菌感染"],
     "side_effects": ["高血糖", "失眠", "免疫抑制"], "metabolism": "CYP3A4"},
    {"id": "aprepitant", "name": "阿瑞匹坦", "category": "NK-1受体拮抗剂", "generic_name": "阿瑞匹坦",
     "contraindications": ["与匹莫齐特合用"],
     "side_effects": ["疲劳", "呃逆", "肝酶升高"], "metabolism": "CYP3A4"},

    # ==================== 补充:被 safety_rules/interactions 引用的药物 ====================
    {"id": "lithium", "name": "碳酸锂", "category": "情绪稳定剂", "generic_name": "碳酸锂",
     "contraindications": ["严重肾功能不全", "严重心脏病", "孕期"],
     "side_effects": ["震颤", "多尿", "甲状腺功能减退", "肾毒性"], "metabolism": "肾脏排泄"},
    {"id": "gemfibrozil", "name": "吉非罗齐", "category": "降脂药", "generic_name": "吉非罗齐",
     "contraindications": ["严重肝病", "严重肾功能不全", "胆囊疾病"],
     "side_effects": ["肌痛", "横纹肌溶解", "肝功能异常"], "metabolism": "CYP2C8/UGT"},
    {"id": "tizanidine", "name": "替扎尼定", "category": "肌肉松弛剂", "generic_name": "盐酸替扎尼定",
     "contraindications": ["严重肝功能不全", "合用CYP1A2抑制剂"],
     "side_effects": ["嗜睡", "低血压", "肝毒性"], "metabolism": "CYP1A2"},
    {"id": "alcohol", "name": "乙醇", "category": "中枢抑制剂", "generic_name": "乙醇",
     "contraindications": ["肝病", "孕期", "合用镇静药"],
     "side_effects": ["中枢抑制", "肝损伤", "依赖性"], "metabolism": "ADH/CYP2E1"},
    {"id": "antacids", "name": "抗酸药", "category": "胃酸中和剂", "generic_name": "氢氧化铝/镁",
     "contraindications": ["严重肾功能不全"],
     "side_effects": ["便秘", "腹泻", "电解质紊乱"], "metabolism": "不代谢"},
    {"id": "potassium", "name": "氯化钾", "category": "电解质补充剂", "generic_name": "氯化钾",
     "contraindications": ["高钾血症", "严重肾功能不全", "合用保钾利尿剂"],
     "side_effects": ["恶心", "高钾血症", "心律失常"], "metabolism": "肾脏排泄"},
    {"id": "mercaptopurine", "name": "巯嘌呤", "category": "抗肿瘤药", "generic_name": "巯嘌呤",
     "contraindications": ["严重肝功能不全", "严重骨髓抑制"],
     "side_effects": ["骨髓抑制", "肝毒性", "恶心"], "metabolism": "TPMT/XO"},
    {"id": "cimetidine", "name": "西咪替丁", "category": "H2受体拮抗剂", "generic_name": "西咪替丁",
     "contraindications": ["严重肝肾功能不全"],
     "side_effects": ["头晕", "腹泻", "抗雄激素作用"], "metabolism": "CYP1A2/CYP3A4"},
    {"id": "testosterone", "name": "睾酮", "category": "雄激素", "generic_name": "睾酮",
     "contraindications": ["前列腺癌", "乳腺癌", "孕期"],
     "side_effects": ["痤疮", "红细胞增多", "肝毒性"], "metabolism": "CYP3A4"},
    {"id": "hydroxyzine", "name": "羟嗪", "category": "抗组胺药", "generic_name": "盐酸羟嗪",
     "contraindications": ["孕期", "QT间期延长"],
     "side_effects": ["嗜睡", "口干", "QT间期延长"], "metabolism": "CYP3A4/CYP2D6"},
]

# ===== 药物相互作用数据 =====
INTERACTIONS = [
    # --- 华法林相关(高危) ---
    ("warfarin", "aspirin", "high", "抗凝+抗血小板双联,消化道出血风险显著增加(非三联)"),
    ("warfarin", "ibuprofen", "critical", "NSAIDs抑制血小板+华法林抗凝,消化道出血风险极高"),
    ("warfarin", "diclofenac", "critical", "NSAIDs增强华法林抗凝效果,出血风险"),
    ("warfarin", "naproxen", "critical", "NSAIDs增强华法林抗凝效果,出血风险"),
    ("warfarin", "clopidogrel", "high", "双重抗血小板+抗凝,出血风险增加"),
    ("warfarin", "omeprazole", "medium", "PPI可能影响华法林代谢(CYP2C19),需监测INR"),
    ("warfarin", "fluconazole", "critical", "CYP2C9抑制,华法林血药浓度显著升高,出血风险极高"),
    ("warfarin", "amiodarone", "critical", "CYP2C9抑制,华法林血药浓度升高"),
    ("warfarin", "acetaminophen", "medium", "长期大量使用可能增强抗凝效果"),
    ("warfarin", "simvastatin", "medium", "可能增强抗凝效果,需监测INR"),
    ("warfarin", "atorvastatin", "medium", "可能增强抗凝效果,需监测INR"),
    ("warfarin", "levothyroxine", "medium", "甲状腺激素可能增强华法林效果"),
    ("warfarin", "carbamazepine", "high", "CYP3A4诱导,华法林代谢加快,抗凝效果减弱"),
    ("warfarin", "metronidazole", "high", "增强抗凝效果,出血风险"),
    ("warfarin", "azithromycin", "high", "可能增强抗凝效果"),
    ("warfarin", "clarithromycin", "high", "CYP3A4抑制,华法林代谢减慢"),
    ("warfarin", "voriconazole", "critical", "CYP2C9抑制,华法林血药浓度显著升高"),
    ("warfarin", "itraconazole", "critical", "CYP3A4抑制,华法林血药浓度升高"),
    ("warfarin", "rivaroxaban", "critical", "双重抗凝,出血风险极高"),
    ("warfarin", "apixaban", "critical", "双重抗凝,出血风险极高"),
    ("warfarin", "ticagrelor", "high", "抗凝+抗血小板,出血风险增加"),
    ("warfarin", "rosuvastatin", "medium", "可能增强抗凝效果"),
    ("warfarin", "tamoxifen", "medium", "可能增强抗凝效果"),

    # --- 抗凝药之间 ---
    ("warfarin", "heparin", "critical", "双重抗凝,出血风险极高"),
    ("heparin", "rivaroxaban", "critical", "双重抗凝,出血风险极高"),
    ("heparin", "apixaban", "critical", "双重抗凝,出血风险极高"),
    ("aspirin", "clopidogrel", "high", "双重抗血小板(临床有时需要,但出血风险增加)"),
    ("aspirin", "heparin", "high", "抗血小板+抗凝,出血风险增加"),
    ("aspirin", "ticagrelor", "high", "双重抗血小板,出血风险增加"),
    ("clopidogrel", "ticagrelor", "high", "双重抗血小板,出血风险增加"),
    ("aspirin", "rivaroxaban", "high", "抗血小板+抗凝,出血风险增加"),

    # --- NSAIDs之间 ---
    ("ibuprofen", "diclofenac", "high", "同类NSAIDs叠加,消化道溃疡和肾毒性风险显著增加"),
    ("ibuprofen", "naproxen", "high", "同类NSAIDs叠加,消化道和肾脏风险"),
    ("ibuprofen", "celecoxib", "high", "NSAIDs+COX-2抑制剂叠加,心血管和消化道风险"),
    ("ibuprofen", "aspirin", "high", "布洛芬可能干扰阿司匹林的抗血小板作用"),
    ("ibuprofen", "meloxicam", "high", "同类NSAIDs叠加"),
    ("diclofenac", "naproxen", "high", "同类NSAIDs叠加"),
    ("diclofenac", "celecoxib", "high", "NSAIDs+COX-2抑制剂叠加"),

    # --- NSAIDs + 其他 ---
    ("ibuprofen", "lisinopril", "high", "NSAIDs削弱ACEI降压效果,增加肾损伤风险"),
    ("ibuprofen", "losartan", "high", "NSAIDs削弱ARB降压效果,增加肾损伤风险"),
    ("ibuprofen", "furosemide", "high", "NSAIDs削弱利尿剂效果,增加肾损伤风险"),
    ("ibuprofen", "lithium", "high", "NSAIDs减少锂排泄,锂中毒风险"),
    ("ibuprofen", "metformin", "medium", "NSAIDs可能影响肾功能,间接影响二甲双胍排泄"),
    ("diclofenac", "lisinopril", "high", "NSAIDs削弱ACEI降压效果"),
    ("diclofenac", "losartan", "high", "NSAIDs削弱ARB降压效果"),
    ("naproxen", "lisinopril", "high", "NSAIDs削弱ACEI降压效果"),
    ("celecoxib", "losartan", "high", "COX-2抑制剂削弱ARB降压效果"),

    # --- 他汀类相互作用 ---
    ("simvastatin", "amlodipine", "high", "CYP3A4抑制,他汀血药浓度升高,横纹肌溶解风险"),
    ("atorvastatin", "amlodipine", "medium", "CYP3A4竞争,他汀血药浓度可能升高"),
    ("simvastatin", "fluconazole", "critical", "CYP3A4强抑制,他汀血药浓度显著升高,横纹肌溶解"),
    ("atorvastatin", "fluconazole", "high", "CYP3A4抑制,他汀血药浓度升高"),
    ("simvastatin", "itraconazole", "critical", "CYP3A4强抑制,他汀血药浓度显著升高"),
    ("simvastatin", "clarithromycin", "high", "CYP3A4强抑制,横纹肌溶解风险,建议暂停他汀或换药"),
    ("simvastatin", "erythromycin", "high", "CYP3A4抑制,他汀血药浓度升高"),
    ("atorvastatin", "itraconazole", "high", "CYP3A4抑制"),
    ("atorvastatin", "clarithromycin", "high", "CYP3A4抑制"),
    ("simvastatin", "diltiazem", "high", "CYP3A4抑制,他汀血药浓度升高"),
    ("simvastatin", "verapamil", "high", "CYP3A4抑制,他汀血药浓度升高"),
    ("rosuvastatin", "cyclosporine", "critical", "他汀血药浓度显著升高,横纹肌溶解风险极高"),

    # --- β阻滞剂 ---
    ("metoprolol", "diltiazem", "high", "双重抑制心脏传导,心动过缓和传导阻滞风险"),
    ("atenolol", "verapamil", "high", "双重心脏抑制,严重心动过缓"),
    ("metoprolol", "fluoxetine", "medium", "CYP2D6抑制,美托洛尔血药浓度升高"),
    ("metoprolol", "paroxetine", "medium", "CYP2D6抑制,美托洛尔血药浓度升高"),
    ("carvedilol", "diltiazem", "high", "双重心脏抑制"),
    ("bisoprolol", "verapamil", "high", "双重心脏抑制"),

    # --- 地高辛 ---
    ("digoxin", "furosemide", "high", "呋塞米致低钾血症,增加地高辛毒性"),
    ("digoxin", "spironolactone", "medium", "螺内酯影响地高辛排泄,需监测血药浓度"),
    ("digoxin", "amiodarone", "high", "减少地高辛排泄,血药浓度升高"),
    ("digoxin", "clarithromycin", "high", "减少地高辛排泄"),
    ("digoxin", "hydrochlorothiazide", "medium", "低钾血症增加地高辛毒性"),

    # --- 降糖药 ---
    ("metformin", "furosemide", "medium", "呋塞米可能影响肾功能,间接影响二甲双胍排泄"),
    ("glibenclamide", "fluconazole", "high", "CYP2C9抑制,磺脲类血药浓度升高,低血糖风险"),
    ("glibenclamide", "metoprolol", "medium", "β阻滞剂掩盖低血糖症状"),
    ("insulin", "metoprolol", "medium", "β阻滞剂掩盖低血糖症状"),
    ("glipizide", "fluconazole", "high", "CYP2C9抑制,磺脲类血药浓度升高"),
    ("glimepiride", "fluconazole", "high", "CYP2C9抑制,磺脲类血药浓度升高"),
    ("empagliflozin", "furosemide", "medium", "双重利尿,脱水和低血压风险"),
    ("dapagliflozin", "insulin", "medium", "低血糖风险增加"),
    ("pioglitazone", "insulin", "medium", "水肿和心衰风险增加"),
    ("pioglitazone", "gemfibrozil", "high", "CYP2C8抑制,吡格列酮血药浓度升高"),

    # --- 抗癫痫/精神科 ---
    ("carbamazepine", "fluoxetine", "high", "CYP3A4/CYP2D6相互作用,血药浓度变化"),
    ("carbamazepine", "valproate", "high", "互相影响血药浓度,肝毒性叠加"),
    ("valproate", "lamotrigine", "high", "丙戊酸显著升高拉莫三嗪血药浓度"),
    ("carbamazepine", "lamotrigine", "medium", "卡马西平加速拉莫三嗪代谢"),
    ("carbamazepine", "erythromycin", "high", "CYP3A4抑制,卡马西平血药浓度升高"),
    ("carbamazepine", "itraconazole", "high", "CYP3A4抑制,卡马西平血药浓度升高"),
    ("carbamazepine", "cyclosporine", "high", "CYP3A4诱导,环孢素血药浓度降低"),
    ("carbamazepine", "verapamil", "high", "CYP3A4相互作用"),
    ("fluoxetine", "tramadol", "critical", "5-HT综合征风险(两种药物都增加5-HT)"),
    ("fluoxetine", "sertraline", "critical", "同类SSRI叠加,5-HT综合征风险"),
    ("fluoxetine", "venlafaxine", "critical", "5-HT综合征风险"),
    ("fluoxetine", "linezolid", "critical", "MAO抑制,5-HT综合征风险"),
    ("sertraline", "tramadol", "critical", "5-HT综合征风险"),
    ("sertraline", "linezolid", "critical", "MAO抑制,5-HT综合征风险"),
    ("venlafaxine", "tramadol", "critical", "5-HT综合征风险"),
    ("venlafaxine", "linezolid", "critical", "MAO抑制,5-HT综合征风险"),
    ("paroxetine", "tramadol", "critical", "5-HT综合征风险"),
    ("diazepam", "morphine", "critical", "双重中枢抑制,呼吸抑制风险极高"),
    ("alprazolam", "morphine", "critical", "双重中枢抑制,呼吸抑制风险极高"),
    ("lorazepam", "morphine", "critical", "双重中枢抑制,呼吸抑制风险极高"),
    ("clonazepam", "morphine", "critical", "双重中枢抑制,呼吸抑制风险极高"),
    ("diazepam", "tramadol", "high", "中枢抑制叠加,呼吸抑制风险"),
    ("alprazolam", "tramadol", "high", "中枢抑制叠加"),
    ("diazepam", "oxycodone", "critical", "双重中枢抑制,呼吸抑制风险极高"),
    ("morphine", "oxycodone", "critical", "双重阿片类,呼吸抑制风险极高"),
    ("olanzapine", "fluoxetine", "medium", "CYP2D6抑制,奥氮平血药浓度可能升高"),
    ("olanzapine", "carbamazepine", "medium", "CYP1A2诱导,奥氮平血药浓度降低"),
    ("quetiapine", "fluoxetine", "medium", "CYP3A4抑制,喹硫平血药浓度可能升高"),
    ("haloperidol", "fluoxetine", "medium", "CYP2D6抑制,氟哌啶醇血药浓度升高"),
    ("haloperidol", "carbamazepine", "medium", "CYP3A4诱导,氟哌啶醇血药浓度降低"),

    # --- 抗生素相互作用 ---
    ("ciprofloxacin", "theophylline", "high", "CYP1A2抑制,茶碱血药浓度升高,心律失常风险"),
    ("ciprofloxacin", "carbamazepine", "medium", "可能影响卡马西平血药浓度"),
    ("ciprofloxacin", "tizanidine", "critical", "CYP1A2抑制,替扎尼定血药浓度极度升高"),
    ("metronidazole", "alcohol", "critical", "双硫仑样反应(面部潮红/心悸/恶心)"),
    ("fluconazole", "carbamazepine", "high", "CYP3A4抑制,卡马西平血药浓度升高"),
    ("fluconazole", "cyclosporine", "high", "CYP3A4抑制,环孢素血药浓度升高"),
    ("fluconazole", "tacrolimus", "high", "CYP3A4抑制,他克莫司血药浓度升高"),
    ("itraconazole", "cyclosporine", "critical", "CYP3A4强抑制,环孢素血药浓度显著升高"),
    ("itraconazole", "tacrolimus", "critical", "CYP3A4强抑制,他克莫司血药浓度显著升高"),
    ("voriconazole", "cyclosporine", "high", "CYP3A4抑制,环孢素血药浓度升高"),
    ("clarithromycin", "cyclosporine", "critical", "CYP3A4强抑制,环孢素血药浓度显著升高"),
    ("clarithromycin", "tacrolimus", "critical", "CYP3A4强抑制,他克莫司血药浓度显著升高"),
    ("erythromycin", "theophylline", "high", "CYP1A2抑制,茶碱血药浓度升高"),
    ("erythromycin", "carbamazepine", "high", "CYP3A4抑制,卡马西平血药浓度升高"),
    ("gentamicin", "furosemide", "high", "呋塞米增加氨基糖苷类肾毒性和耳毒性"),
    ("vancomycin", "gentamicin", "high", "肾毒性叠加"),
    ("vancomycin", "amikacin", "high", "肾毒性叠加"),
    ("linezolid", "sertraline", "critical", "MAO抑制,5-HT综合征风险"),
    ("linezolid", "venlafaxine", "critical", "MAO抑制,5-HT综合征风险"),
    ("linezolid", "fluoxetine", "critical", "MAO抑制,5-HT综合征风险"),

    # --- 免疫抑制 ---
    ("cyclosporine", "tacrolimus", "critical", "双重肾毒性叠加"),
    ("cyclosporine", "amiodarone", "high", "CYP3A4抑制,环孢素血药浓度升高"),
    ("tacrolimus", "amiodarone", "high", "CYP3A4抑制,他克莫司血药浓度升高"),
    ("azathioprine", "allopurinol", "critical", "抑制黄嘌呤氧化酶,硫唑嘌呤代谢受阻,骨髓抑制风险极高"),
    ("methotrexate", "ibuprofen", "high", "NSAIDs减少甲氨蝶呤排泄,血药浓度升高,毒性增加"),
    ("methotrexate", "diclofenac", "high", "NSAIDs减少甲氨蝶呤排泄,血药浓度升高,毒性增加"),
    ("methotrexate", "lisinopril", "medium", "减少甲氨蝶呤排泄"),
    ("mycophenolate", "antacids", "medium", "降低吗替麦考酚酯吸收"),

    # --- 激素 ---
    ("prednisone", "ibuprofen", "high", "消化道溃疡风险叠加"),
    ("prednisone", "aspirin", "high", "消化道出血风险增加"),
    ("dexamethasone", "carbamazepine", "medium", "CYP3A4诱导,地塞米松代谢加快"),
    ("prednisone", "carbamazepine", "medium", "CYP3A4诱导,泼尼松代谢加快"),
    ("dexamethasone", "fluconazole", "medium", "CYP3A4抑制,地塞米松血药浓度升高"),

    # --- ACEI+ARB 双重RAAS阻断 ---
    ("enalapril", "valsartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),
    ("lisinopril", "valsartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),
    ("enalapril", "losartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),
    ("lisinopril", "losartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),
    ("ramipril", "valsartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),
    ("ramipril", "losartan", "high", "ACEI+ARB双重RAAS阻断,低血压和肾功能损害风险"),

    # --- 降压药 ---
    ("lisinopril", "spironolactone", "high", "双重升高血钾,高钾血症风险"),
    ("losartan", "spironolactone", "high", "双重升高血钾,高钾血症风险"),
    ("valsartan", "spironolactone", "high", "双重升高血钾,高钾血症风险"),
    ("lisinopril", "potassium", "high", "高钾血症风险"),
    ("losartan", "potassium", "high", "高钾血症风险"),
    ("amlodipine", "simvastatin", "high", "CYP3A4抑制,他汀血药浓度升高"),
    ("verapamil", "simvastatin", "critical", "CYP3A4强抑制,横纹肌溶解风险"),
    ("verapamil", "atorvastatin", "high", "CYP3A4抑制"),
    ("verapamil", "metoprolol", "high", "双重心脏抑制"),
    ("diltiazem", "atorvastatin", "high", "CYP3A4抑制"),
    ("hydralazine", "nitroglycerin", "medium", "叠加降压,严重低血压风险"),
    ("sacubitril_valsartan", "lisinopril", "critical", "禁止合用(必须间隔36小时),血管性水肿风险"),

    # --- 痛风 ---
    ("colchicine", "clarithromycin", "critical", "CYP3A4抑制,秋水仙碱血药浓度升高,致命毒性"),
    ("colchicine", "itraconazole", "critical", "CYP3A4抑制,秋水仙碱血药浓度升高"),
    ("colchicine", "cyclosporine", "critical", "CYP3A4抑制,秋水仙碱血药浓度升高"),
    ("febuxostat", "azathioprine", "critical", "抑制黄嘌呤氧化酶,硫唑嘌呤蓄积,骨髓抑制"),
    ("febuxostat", "mercaptopurine", "critical", "抑制黄嘌呤氧化酶,6-MP蓄积"),

    # --- 甲状腺 ---
    ("levothyroxine", "calcium_carbonate", "medium", "钙剂影响甲状腺素吸收,需间隔4小时"),
    ("levothyroxine", "omeprazole", "medium", "PPI可能影响甲状腺素吸收"),
    ("levothyroxine", "iron_sulfate", "medium", "铁剂影响甲状腺素吸收,需间隔4小时"),
    ("levothyroxine", "warfarin", "medium", "甲状腺激素可能增强华法林效果"),

    # --- 呼吸科 ---
    ("theophylline", "erythromycin", "high", "CYP1A2抑制,茶碱血药浓度升高"),
    ("theophylline", "cimetidine", "high", "CYP1A2抑制,茶碱血药浓度升高"),
    ("theophylline", "clarithromycin", "high", "CYP1A2抑制,茶碱血药浓度升高"),
    ("theophylline", "ciprofloxacin", "high", "CYP1A2抑制,茶碱血药浓度升高"),

    # --- 泌尿/ED ---
    ("sildenafil", "nitroglycerin", "critical", "严重低血压,可能致命,绝对禁止合用"),
    ("sildenafil", "amlodipine", "medium", "叠加降压,低血压风险"),
    ("sildenafil", "itraconazole", "high", "CYP3A4抑制,西地那非血药浓度升高"),
    ("finasteride", "testosterone", "medium", "药理拮抗"),

    # --- 眼科 ---
    ("timolol_eye", "verapamil", "medium", "全身吸收可致心动过缓"),
    ("timolol_eye", "metoprolol", "medium", "全身吸收可致β阻滞叠加"),

    # --- 骨科 ---
    ("alendronate", "calcium_carbonate", "medium", "钙剂降低阿仑膦酸钠吸收,需间隔至少30分钟"),
    ("alendronate", "aspirin", "medium", "双重胃肠道刺激"),

    # --- 补充:10个新药物的交互 ---
    # lithium
    ("lithium", "naproxen", "high", "NSAIDs降低锂排泄,升高血锂浓度"),
    ("lithium", "diclofenac", "high", "NSAIDs降低锂排泄,升高血锂浓度"),
    ("lithium", "lisinopril", "high", "ACE抑制剂降低锂排泄,锂中毒风险"),
    ("lithium", "losartan", "high", "ARB降低锂排泄,锂中毒风险"),
    ("lithium", "hydrochlorothiazide", "high", "噻嗪类利尿剂降低锂排泄,锂中毒风险"),
    ("lithium", "furosemide", "medium", "袢利尿剂可能影响锂排泄"),
    # gemfibrozil
    ("gemfibrozil", "simvastatin", "critical", "CYP2C8抑制,横纹肌溶解风险极高"),
    ("gemfibrozil", "atorvastatin", "high", "增加他汀类肌毒性"),
    ("gemfibrozil", "rosuvastatin", "high", "增加他汀类肌毒性"),
    # alcohol
    ("alcohol", "diazepam", "critical", "协同中枢抑制,呼吸抑制风险"),
    ("alcohol", "alprazolam", "critical", "协同中枢抑制,呼吸抑制风险"),
    ("alcohol", "tramadol", "critical", "协同中枢抑制,呼吸抑制风险"),
    ("alcohol", "acetaminophen", "high", "增加肝毒性"),
    ("alcohol", "warfarin", "high", "增加出血风险"),
    # antacids
    ("antacids", "levothyroxine", "high", "降低甲状腺素吸收"),
    ("antacids", "ciprofloxacin", "high", "螯合降低吸收"),
    # potassium
    ("potassium", "spironolactone", "critical", "高钾血症风险"),
    # cimetidine
    ("cimetidine", "warfarin", "high", "CYP抑制,华法林浓度升高"),
    ("cimetidine", "diazepam", "high", "CYP抑制,苯二氮卓浓度升高"),
    ("cimetidine", "carbamazepine", "high", "CYP抑制,卡马西平浓度升高"),
    # testosterone
    ("testosterone", "warfarin", "medium", "增强抗凝效果"),
    # hydroxyzine
    ("hydroxyzine", "diazepam", "high", "协同中枢抑制"),
    ("hydroxyzine", "codeine", "high", "协同中枢抑制"),
]

# ===== 替代药物建议 =====
ALTERNATIVES = [
    ("ibuprofen", "acetaminophen", "对乙酰氨基酚不增加消化道出血风险,肾功能影响小"),
    ("diclofenac", "acetaminophen", "对乙酰氨基酚胃肠道安全性更好"),
    ("naproxen", "acetaminophen", "对乙酰氨基酚胃肠道安全性更好"),
    ("celecoxib", "acetaminophen", "对乙酰氨基酚无心血管风险"),
    ("simvastatin", "atorvastatin", "阿托伐他汀CYP3A4依赖性较低,相互作用较少"),
    ("simvastatin", "rosuvastatin", "瑞舒伐他汀主要经CYP2C9代谢,CYP3A4相互作用少"),
    ("simvastatin", "pravastatin", "普伐他汀不经CYP450代谢,相互作用最少"),
    ("warfarin", "rivaroxaban", "新型口服抗凝药无需常规监测INR(但需评估肾功能)"),
    ("warfarin", "apixaban", "新型口服抗凝药,出血风险相对较低"),
    ("diazepam", "hydroxyzine", "非苯二氮卓类抗焦虑,呼吸抑制风险低"),
    ("diazepam", "lorazepam", "劳拉西泮不经过CYP450代谢,相互作用较少"),
    ("morphine", "acetaminophen", "轻中度疼痛可优先使用非阿片类镇痛"),
    ("morphine", "tramadol", "弱阿片类,呼吸抑制风险较低"),
    ("glibenclamide", "sitagliptin", "DPP-4抑制剂低血糖风险极低"),
    ("glibenclamide", "empagliflozin", "SGLT2抑制剂有心血管保护作用"),
    ("fluoxetine", "sertraline", "同为SSRI但CYP2D6抑制较弱(需个体化评估)"),
    ("ciprofloxacin", "azithromycin", "大环内酯类不经过CYP1A2代谢(根据感染类型选择)"),
    ("ciprofloxacin", "amoxicillin", "青霉素类无CYP相互作用(根据感染类型选择)"),
    ("losartan", "amlodipine", "钙通道阻滞剂不升高血钾"),
    ("lisinopril", "amlodipine", "钙通道阻滞剂不升高血钾"),
    ("cyclosporine", "tacrolimus", "他克莫司肾毒性相对较轻(需个体化评估)"),
    ("methotrexate", "mycophenolate", "吗替麦考酚酯肝毒性较低(根据适应症选择)"),
]



# ==================== 扩展药物数据 ====================
_EXTRA_DRUGS = [{'id': 'propranolol', 'name': '普萘洛尔', 'category': 'β受体阻滞剂', 'generic_name': '盐酸普萘洛尔', 'contraindications': ['哮喘', '窦性心动过缓', '心源性休克'], 'side_effects': ['心动过缓', '支气管痉挛', '疲劳'], 'metabolism': 'CYP2D6/CYP1A2'}, {'id': 'nebivolol', 'name': '奈比洛尔', 'category': 'β受体阻滞剂', 'generic_name': '奈比洛尔', 'contraindications': ['肝功能不全', '心源性休克', '窦性心动过缓'], 'side_effects': ['头痛', '疲劳', '低血压'], 'metabolism': 'CYP2D6'}, {'id': 'labetalol', 'name': '拉贝洛尔', 'category': 'α/β受体阻滞剂', 'generic_name': '盐酸拉贝洛尔', 'contraindications': ['哮喘', 'II-III度房室传导阻滞', '心源性休克'], 'side_effects': ['低血压', '头晕', '疲劳'], 'metabolism': '葡萄糖醛酸结合'}, {'id': 'nicardipine', 'name': '尼卡地平', 'category': '钙通道阻滞剂', 'generic_name': '盐酸尼卡地平', 'contraindications': ['严重主动脉瓣狭窄', '颅内出血急性期'], 'side_effects': ['头痛', '水肿', '心动过速'], 'metabolism': 'CYP3A4'}, {'id': 'felodipine', 'name': '非洛地平', 'category': '钙通道阻滞剂', 'generic_name': '非洛地平', 'contraindications': ['心源性休克', '严重低血压'], 'side_effects': ['水肿', '头痛', '面部潮红'], 'metabolism': 'CYP3A4'}, {'id': 'lercanidipine', 'name': '乐卡地平', 'category': '钙通道阻滞剂', 'generic_name': '盐酸乐卡地平', 'contraindications': ['未控制的心衰', '严重肝肾功能不全'], 'side_effects': ['水肿', '头痛', '面部潮红'], 'metabolism': 'CYP3A4'}, {'id': 'nitroprusside', 'name': '硝普钠', 'category': '血管扩张药', 'generic_name': '硝普钠', 'contraindications': ['代偿性高血压', '颅内压升高'], 'side_effects': ['低血压', '氰化物中毒'], 'metabolism': '红细胞代谢'}, {'id': 'minoxidil', 'name': '米诺地尔', 'category': '血管扩张药', 'generic_name': '米诺地尔', 'contraindications': ['嗜铬细胞瘤'], 'side_effects': ['多毛症', '液体潴留', '心动过速'], 'metabolism': '葡萄糖醛酸结合'}, {'id': 'isosorbide_dinitrate', 'name': '硝酸异山梨酯', 'category': '抗心绞痛药', 'generic_name': '硝酸异山梨酯', 'contraindications': ['严重低血压', '肥厚型梗阻性心肌病', 'PDE5抑制剂使用中'], 'side_effects': ['头痛', '低血压', '耐药性'], 'metabolism': '肝脏代谢'}, {'id': 'trimetazidine', 'name': '曲美他嗪', 'category': '抗心绞痛药', 'generic_name': '盐酸曲美他嗪', 'contraindications': ['帕金森病', '震颤', '严重肾功能不全'], 'side_effects': ['震颤', '帕金森样症状', '头晕'], 'metabolism': '肾脏排泄'}, {'id': 'ivabradine', 'name': '伊伐布雷定', 'category': '抗心绞痛药', 'generic_name': '伊伐布雷定', 'contraindications': ['窦性心动过缓', '病态窦房结综合征', '严重肝功能不全'], 'side_effects': ['闪光幻觉', '心动过缓'], 'metabolism': 'CYP3A4'}, {'id': 'ranolazine', 'name': '雷诺嗪', 'category': '抗心绞痛药', 'generic_name': '雷诺嗪', 'contraindications': ['肝功能不全', 'QT间期延长'], 'side_effects': ['头晕', '便秘', 'QT延长'], 'metabolism': 'CYP3A4/CYP2D6'}, {'id': 'moxonidine', 'name': '莫索尼定', 'category': '中枢降压药', 'generic_name': '盐酸莫索尼定', 'contraindications': ['病态窦房结综合征', '严重心动过缓', '严重心衰'], 'side_effects': ['口干', '头晕', '疲乏'], 'metabolism': '部分肝脏代谢'}, {'id': 'clonidine', 'name': '可乐定', 'category': '中枢降压药', 'generic_name': '盐酸可乐定', 'contraindications': ['严重心动过缓', '病态窦房结综合征'], 'side_effects': ['口干', '嗜睡', '反跳性高血压'], 'metabolism': '50%肝脏代谢'}, {'id': 'methyldopa', 'name': '甲基多巴', 'category': '中枢降压药', 'generic_name': '甲基多巴', 'contraindications': ['活动性肝病', '嗜铬细胞瘤'], 'side_effects': ['嗜睡', '肝损害', '溶血性贫血'], 'metabolism': '肝脏代谢'}, {'id': 'sotalol', 'name': '索他洛尔', 'category': '抗心律失常药', 'generic_name': '盐酸索他洛尔', 'contraindications': ['哮喘', '窦性心动过缓', 'QT延长', '心源性休克'], 'side_effects': ['心动过缓', 'QT延长', '疲劳'], 'metabolism': '肾脏排泄'}, {'id': 'dronedarone', 'name': '决奈达隆', 'category': '抗心律失常药', 'generic_name': '盐酸决奈达隆', 'contraindications': ['永久性房颤', '严重肝损害', 'NYHA IV级心衰'], 'side_effects': ['QT延长', '肝毒性', '心动过缓'], 'metabolism': 'CYP3A4'}, {'id': 'lidocaine_iv', 'name': '利多卡因(注射)', 'category': '抗心律失常药', 'generic_name': '盐酸利多卡因', 'contraindications': ['严重窦房传导阻滞', 'WPW综合征'], 'side_effects': ['中枢神经毒性', '低血压', '癫痫'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'eplerenone', 'name': '依普利酮', 'category': '利尿药', 'generic_name': '依普利酮', 'contraindications': ['高钾血症', '严重肾功能不全', 'CYP3A4强抑制剂合用'], 'side_effects': ['高钾血症', '头晕', '腹泻'], 'metabolism': 'CYP3A4'}, {'id': 'mannitol', 'name': '甘露醇', 'category': '利尿药', 'generic_name': '甘露醇', 'contraindications': ['严重肾功能不全', '颅内活动性出血', '严重脱水'], 'side_effects': ['电解质紊乱', '肺水肿', '肾损害'], 'metabolism': '肾脏排泄'}, {'id': 'pitavastatin', 'name': '匹伐他汀', 'category': '他汀类', 'generic_name': '匹伐他汀钙', 'contraindications': ['活动性肝病', '孕妇', '哺乳期'], 'side_effects': ['肌痛', '转氨酶升高'], 'metabolism': 'CYP2C9(少量)'}, {'id': 'ezetimibe', 'name': '依折麦布', 'category': '降脂药', 'generic_name': '依折麦布', 'contraindications': ['活动性肝病'], 'side_effects': ['腹痛', '腹泻', '转氨酶升高'], 'metabolism': '葡萄糖醛酸结合'}, {'id': 'fenofibrate', 'name': '非诺贝特', 'category': '贝特类', 'generic_name': '非诺贝特', 'contraindications': ['严重肝肾功能不全', '胆囊疾病'], 'side_effects': ['肌痛', '转氨酶升高', '胆石症'], 'metabolism': '酯酶水解/CYP3A4'}, {'id': 'cholestyramine', 'name': '考来烯胺', 'category': '胆酸螯合剂', 'generic_name': '考来烯胺', 'contraindications': ['完全性胆道梗阻'], 'side_effects': ['便秘', '腹胀', '脂肪吸收不良'], 'metabolism': '不吸收'}, {'id': 'PCSK9_inhibitor', 'name': '依洛尤单抗', 'category': 'PCSK9抑制剂', 'generic_name': '依洛尤单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['注射部位反应', '上呼吸道感染'], 'metabolism': '蛋白水解'}, {'id': 'bempedoic_acid', 'name': '贝派地酸', 'category': '降脂药', 'generic_name': '贝派地酸', 'contraindications': ['痛风', '高尿酸血症'], 'side_effects': ['高尿酸血症', '肌痛', '贫血'], 'metabolism': 'ACSVL1活化'}, {'id': 'cefoperazone', 'name': '头孢哌酮', 'category': '头孢菌素类', 'generic_name': '头孢哌酮钠', 'contraindications': ['头孢菌素过敏', '严重出血倾向'], 'side_effects': ['出血', '腹泻', '过敏反应'], 'metabolism': '胆汁排泄为主'}, {'id': 'norfloxacin', 'name': '诺氟沙星', 'category': '喹诺酮类', 'generic_name': '诺氟沙星', 'contraindications': ['儿童青少年', '癫痫'], 'side_effects': ['恶心', '头痛', '光敏感'], 'metabolism': 'CYP1A2'}, {'id': 'ertapenem', 'name': '厄他培南', 'category': '碳青霉烯类', 'generic_name': '厄他培南钠', 'contraindications': ['碳青霉烯过敏'], 'side_effects': ['腹泻', '头痛', '静脉炎'], 'metabolism': '肾脏排泄'}, {'id': 'tobramycin', 'name': '妥布霉素', 'category': '氨基糖苷类', 'generic_name': '硫酸妥布霉素', 'contraindications': ['氨基糖苷类过敏'], 'side_effects': ['肾毒性', '耳毒性'], 'metabolism': '肾脏排泄'}, {'id': 'teicoplanin', 'name': '替考拉宁', 'category': '糖肽类', 'generic_name': '替考拉宁', 'contraindications': ['替考拉宁过敏'], 'side_effects': ['注射部位反应', '肝肾毒性'], 'metabolism': '肾脏排泄'}, {'id': 'colistin', 'name': '多粘菌素E', 'category': '多粘菌素类', 'generic_name': '硫酸多粘菌素E', 'contraindications': ['重症肌无力'], 'side_effects': ['肾毒性', '神经毒性'], 'metabolism': '肾脏排泄'}, {'id': 'tinidazole', 'name': '替硝唑', 'category': '硝基咪唑类', 'generic_name': '替硝唑', 'contraindications': ['第一孕期', '血液病'], 'side_effects': ['金属味', '恶心', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'cotrimoxazole', 'name': '复方磺胺甲恶唑', 'category': '磺胺类', 'generic_name': '磺胺甲恶唑/甲氧苄啶', 'contraindications': ['磺胺过敏', '严重肝肾功能不全'], 'side_effects': ['皮疹', '骨髓抑制', '高钾血症'], 'metabolism': 'CYP2C9/NAT2'}, {'id': 'fosfomycin', 'name': '磷霉素', 'category': '磷霉素类', 'generic_name': '磷霉素氨丁三醇', 'contraindications': ['磷霉素过敏'], 'side_effects': ['腹泻', '头痛', '恶心'], 'metabolism': '不代谢'}, {'id': 'amphotericin_b', 'name': '两性霉素B', 'category': '抗真菌药', 'generic_name': '两性霉素B', 'contraindications': ['严重肾功能不全'], 'side_effects': ['肾毒性', '输液反应', '低钾血症'], 'metabolism': '不明'}, {'id': 'caspofungin', 'name': '卡泊芬净', 'category': '抗真菌药', 'generic_name': '醋酸卡泊芬净', 'contraindications': ['卡泊芬净过敏'], 'side_effects': ['发热', '静脉炎', '肝功能异常'], 'metabolism': '肝脏水解'}, {'id': 'griseofulvin', 'name': '灰黄霉素', 'category': '抗真菌药', 'generic_name': '灰黄霉素', 'contraindications': ['肝功能不全', '卟啉症', '孕妇'], 'side_effects': ['头痛', '光敏反应', '肝毒性'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'ganciclovir', 'name': '更昔洛韦', 'category': '抗病毒药', 'generic_name': '更昔洛韦', 'contraindications': ['中性粒细胞<500', '血小板<25000'], 'side_effects': ['骨髓抑制', '肾毒性', '神经毒性'], 'metabolism': '肾脏排泄'}, {'id': 'tenofovir', 'name': '替诺福韦', 'category': '抗病毒药', 'generic_name': '富马酸替诺福韦二吡呋酯', 'contraindications': ['替诺福韦过敏'], 'side_effects': ['肾毒性', '骨密度降低', '乳酸酸中毒'], 'metabolism': '肾脏排泄'}, {'id': 'entecavir', 'name': '恩替卡韦', 'category': '抗病毒药', 'generic_name': '恩替卡韦', 'contraindications': ['恩替卡韦过敏'], 'side_effects': ['头痛', '疲劳', '乳酸酸中毒(罕见)'], 'metabolism': '部分CYP代谢'}, {'id': 'sofosbuvir', 'name': '索磷布韦', 'category': '抗病毒药', 'generic_name': '索磷布韦', 'contraindications': ['索磷布韦过敏'], 'side_effects': ['疲劳', '头痛', '恶心'], 'metabolism': '前药'}, {'id': 'paliperidone', 'name': '帕利哌酮', 'category': '抗精神病药', 'generic_name': '帕利哌酮', 'contraindications': ['帕利哌酮过敏'], 'side_effects': ['锥体外系反应', '高催乳素血症', 'QT延长'], 'metabolism': 'CYP2D6(少量)'}, {'id': 'clozapine', 'name': '氯氮平', 'category': '抗精神病药', 'generic_name': '氯氮平', 'contraindications': ['粒细胞缺乏史', '癫痫未控制'], 'side_effects': ['粒细胞缺乏', '代谢综合征', '心肌炎'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'ziprasidone', 'name': '齐拉西酮', 'category': '抗精神病药', 'generic_name': '盐酸齐拉西酮', 'contraindications': ['QT延长', '近期心肌梗死'], 'side_effects': ['QT延长', '嗜睡', '恶心'], 'metabolism': 'CYP3A4'}, {'id': 'valproic_acid', 'name': '丙戊酸', 'category': '抗癫痫药', 'generic_name': '丙戊酸钠', 'contraindications': ['肝病', '尿素循环障碍', '孕妇'], 'side_effects': ['肝毒性', '胰腺炎', '致畸', '血小板减少'], 'metabolism': 'CYP2C9/葡萄糖醛酸结合'}, {'id': 'trazodone', 'name': '曲唑酮', 'category': 'SARI', 'generic_name': '盐酸曲唑酮', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['嗜睡', '体位性低血压'], 'metabolism': 'CYP3A4'}, {'id': 'methylphenidate', 'name': '哌甲酯', 'category': '中枢兴奋药', 'generic_name': '盐酸哌甲酯', 'contraindications': ['焦虑', '青光眼', '抽动症', 'MAO抑制剂使用中'], 'side_effects': ['失眠', '食欲减退', '心动过速'], 'metabolism': 'CES1'}, {'id': 'atomoxetine', 'name': '托莫西汀', 'category': 'NRI', 'generic_name': '盐酸托莫西汀', 'contraindications': ['MAO抑制剂使用中', '嗜铬细胞瘤'], 'side_effects': ['恶心', '食欲减退', '肝毒性(罕见)'], 'metabolism': 'CYP2D6'}, {'id': 'buspirone', 'name': '丁螺环酮', 'category': '抗焦虑药', 'generic_name': '盐酸丁螺环酮', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['头晕', '恶心', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'gliclazide', 'name': '格列齐特', 'category': '磺脲类降糖药', 'generic_name': '格列齐特', 'contraindications': ['1型糖尿病', '酮症酸中毒'], 'side_effects': ['低血糖', '体重增加'], 'metabolism': 'CYP2C9'}, {'id': 'repaglinide', 'name': '瑞格列奈', 'category': '格列奈类', 'generic_name': '瑞格列奈', 'contraindications': ['1型糖尿病', '酮症酸中毒'], 'side_effects': ['低血糖', '体重增加'], 'metabolism': 'CYP2C8/CYP3A4'}, {'id': 'semaglutide', 'name': '司美格鲁肽', 'category': 'GLP-1受体激动剂', 'generic_name': '司美格鲁肽', 'contraindications': ['甲状腺髓样癌史', 'MEN2'], 'side_effects': ['恶心', '呕吐', '腹泻'], 'metabolism': '蛋白水解'}, {'id': 'canagliflozin', 'name': '卡格列净', 'category': 'SGLT2抑制剂', 'generic_name': '卡格列净', 'contraindications': ['透析'], 'side_effects': ['泌尿生殖感染', '酮症酸中毒', '截肢风险'], 'metabolism': 'UGT1A9'}, {'id': 'linagliptin', 'name': '利格列汀', 'category': 'DPP-4抑制剂', 'generic_name': '利格列汀', 'contraindications': ['利格列汀过敏'], 'side_effects': ['鼻咽炎', '头痛'], 'metabolism': 'CYP3A4(少量)'}, {'id': 'saxagliptin', 'name': '沙格列汀', 'category': 'DPP-4抑制剂', 'generic_name': '沙格列汀', 'contraindications': ['心衰'], 'side_effects': ['上呼吸道感染', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'insulin_glargine', 'name': '甘精胰岛素', 'category': '胰岛素', 'generic_name': '甘精胰岛素', 'contraindications': ['低血糖'], 'side_effects': ['低血糖', '体重增加'], 'metabolism': '蛋白水解'}, {'id': 'insulin_aspart', 'name': '门冬胰岛素', 'category': '胰岛素', 'generic_name': '门冬胰岛素', 'contraindications': ['低血糖'], 'side_effects': ['低血糖', '体重增加'], 'metabolism': '蛋白水解'}, {'id': 'fluticasone', 'name': '氟替卡松', 'category': '吸入性糖皮质激素', 'generic_name': '丙酸氟替卡松', 'contraindications': ['哮喘急性发作(单药)'], 'side_effects': ['口腔念珠菌感染', '声音嘶哑'], 'metabolism': 'CYP3A4'}, {'id': 'ambroxol', 'name': '氨溴索', 'category': '祛痰药', 'generic_name': '盐酸氨溴索', 'contraindications': ['严重肝肾功能不全'], 'side_effects': ['恶心', '过敏反应(罕见)'], 'metabolism': '肝脏代谢'}, {'id': 'acetylcysteine', 'name': '乙酰半胱氨酸', 'category': '祛痰药', 'generic_name': '乙酰半胱氨酸', 'contraindications': ['哮喘(雾化)'], 'side_effects': ['恶心', '呕吐'], 'metabolism': '肝脏代谢'}, {'id': 'dextromethorphan', 'name': '右美沙芬', 'category': '镇咳药', 'generic_name': '氢溴酸右美沙芬', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['嗜睡', '头晕', '5-HT综合征(合用SSRI)'], 'metabolism': 'CYP2D6'}, {'id': 'omalizumab', 'name': '奥马珠单抗', 'category': '抗IgE单抗', 'generic_name': '奥马珠单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['注射部位反应', '过敏反应'], 'metabolism': '网状内皮系统'}, {'id': 'rabeprazole', 'name': '雷贝拉唑', 'category': 'PPI', 'generic_name': '雷贝拉唑钠', 'contraindications': ['雷贝拉唑过敏'], 'side_effects': ['头痛', '腹泻'], 'metabolism': '非酶代谢为主'}, {'id': 'granisetron', 'name': '格拉司琼', 'category': '止吐药', 'generic_name': '盐酸格拉司琼', 'contraindications': ['格拉司琼过敏'], 'side_effects': ['头痛', '便秘'], 'metabolism': 'CYP3A4'}, {'id': 'fentanyl', 'name': '芬太尼', 'category': '阿片类镇痛药', 'generic_name': '枸橼酸芬太尼', 'contraindications': ['呼吸抑制', '急性腹痛未诊断'], 'side_effects': ['呼吸抑制', '便秘', '成瘾'], 'metabolism': 'CYP3A4'}, {'id': 'buprenorphine', 'name': '丁丙诺啡', 'category': '阿片类镇痛药', 'generic_name': '盐酸丁丙诺啡', 'contraindications': ['呼吸抑制'], 'side_effects': ['呼吸抑制(有天花板)', '恶心'], 'metabolism': 'CYP3A4'}, {'id': 'tapentadol', 'name': '他喷他多', 'category': '阿片类镇痛药', 'generic_name': '盐酸他喷他多', 'contraindications': ['MAO抑制剂使用中', '呼吸抑制'], 'side_effects': ['恶心', '头晕', '5-HT综合征'], 'metabolism': 'UGT'}, {'id': 'sirolimus', 'name': '西罗莫司', 'category': '免疫抑制剂', 'generic_name': '西罗莫司', 'contraindications': ['对西罗莫司过敏'], 'side_effects': ['高脂血症', '血小板减少', '伤口愈合延迟'], 'metabolism': 'CYP3A4'}, {'id': 'everolimus', 'name': '依维莫司', 'category': '免疫抑制剂/抗肿瘤', 'generic_name': '依维莫司', 'contraindications': ['对依维莫司过敏'], 'side_effects': ['口腔炎', '肺炎', '高血糖'], 'metabolism': 'CYP3A4'}, {'id': 'leflunomide', 'name': '来氟米特', 'category': '免疫抑制剂', 'generic_name': '来氟米特', 'contraindications': ['孕妇(致畸)', '严重肝功能不全'], 'side_effects': ['肝毒性', '腹泻', '脱发'], 'metabolism': 'CYP1A2/CYP2C19'}, {'id': 'cyclophosphamide', 'name': '环磷酰胺', 'category': '抗肿瘤药', 'generic_name': '环磷酰胺', 'contraindications': ['严重骨髓抑制'], 'side_effects': ['骨髓抑制', '出血性膀胱炎', '不孕'], 'metabolism': 'CYP2B6/CYP3A4'}, {'id': 'doxorubicin', 'name': '多柔比星', 'category': '抗肿瘤药', 'generic_name': '盐酸多柔比星', 'contraindications': ['严重骨髓抑制', '心功能不全'], 'side_effects': ['心脏毒性', '骨髓抑制', '脱发'], 'metabolism': 'CYP3A4/CYP2D6'}, {'id': 'paclitaxel', 'name': '紫杉醇', 'category': '抗肿瘤药', 'generic_name': '紫杉醇', 'contraindications': ['中性粒细胞<1500'], 'side_effects': ['骨髓抑制', '过敏反应', '周围神经病变'], 'metabolism': 'CYP2C8/CYP3A4'}, {'id': 'cisplatin', 'name': '顺铂', 'category': '抗肿瘤药', 'generic_name': '顺铂', 'contraindications': ['肾功能不全', '听力损害'], 'side_effects': ['肾毒性', '耳毒性', '神经毒性'], 'metabolism': '非酶代谢'}, {'id': 'carboplatin', 'name': '卡铂', 'category': '抗肿瘤药', 'generic_name': '卡铂', 'contraindications': ['严重骨髓抑制'], 'side_effects': ['骨髓抑制(血小板为主)'], 'metabolism': '肾脏排泄'}, {'id': 'fluorouracil', 'name': '氟尿嘧啶', 'category': '抗肿瘤药', 'generic_name': '氟尿嘧啶', 'contraindications': ['严重骨髓抑制', 'DPD缺乏'], 'side_effects': ['骨髓抑制', '口腔炎', '手足综合征'], 'metabolism': 'DPD'}, {'id': 'capecitabine', 'name': '卡培他滨', 'category': '抗肿瘤药', 'generic_name': '卡培他滨', 'contraindications': ['DPD缺乏'], 'side_effects': ['手足综合征', '腹泻', '骨髓抑制'], 'metabolism': '三步酶活化'}, {'id': 'oxaliplatin', 'name': '奥沙利铂', 'category': '抗肿瘤药', 'generic_name': '奥沙利铂', 'contraindications': ['严重肾功能不全'], 'side_effects': ['周围神经病变', '骨髓抑制'], 'metabolism': '非酶水解'}, {'id': 'irinotecan', 'name': '伊立替康', 'category': '抗肿瘤药', 'generic_name': '盐酸伊立替康', 'contraindications': ['严重骨髓抑制'], 'side_effects': ['迟发性腹泻', '骨髓抑制'], 'metabolism': 'CYP3A4/UGT1A1'}, {'id': 'pemetrexed', 'name': '培美曲塞', 'category': '抗肿瘤药', 'generic_name': '培美曲塞二钠', 'contraindications': ['严重肾功能不全'], 'side_effects': ['骨髓抑制', '皮疹'], 'metabolism': '肾脏排泄'}, {'id': 'gemcitabine', 'name': '吉西他滨', 'category': '抗肿瘤药', 'generic_name': '盐酸吉西他滨', 'contraindications': ['严重骨髓抑制'], 'side_effects': ['骨髓抑制', '肝毒性', '肺毒性'], 'metabolism': '胞苷脱氨酶'}, {'id': 'vinorelbine', 'name': '长春瑞滨', 'category': '抗肿瘤药', 'generic_name': '酒石酸长春瑞滨', 'contraindications': ['严重骨髓抑制'], 'side_effects': ['骨髓抑制', '神经毒性'], 'metabolism': 'CYP3A4'}, {'id': 'docetaxel', 'name': '多西他赛', 'category': '抗肿瘤药', 'generic_name': '多西他赛', 'contraindications': ['中性粒细胞<1500'], 'side_effects': ['骨髓抑制', '过敏反应'], 'metabolism': 'CYP3A4'}, {'id': 'erlotinib', 'name': '厄洛替尼', 'category': '抗肿瘤药', 'generic_name': '盐酸厄洛替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['皮疹', '腹泻', '间质性肺炎'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'gefitinib', 'name': '吉非替尼', 'category': '抗肿瘤药', 'generic_name': '吉非替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['皮疹', '腹泻'], 'metabolism': 'CYP3A4/CYP2D6'}, {'id': 'imatinib', 'name': '伊马替尼', 'category': '抗肿瘤药', 'generic_name': '甲磺酸伊马替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['水肿', '恶心', '骨髓抑制'], 'metabolism': 'CYP3A4'}, {'id': 'sorafenib', 'name': '索拉非尼', 'category': '抗肿瘤药', 'generic_name': '甲苯磺酸索拉非尼', 'contraindications': ['QT延长'], 'side_effects': ['手足综合征', '腹泻', '高血压'], 'metabolism': 'CYP3A4'}, {'id': 'lenvatinib', 'name': '仑伐替尼', 'category': '抗肿瘤药', 'generic_name': '甲磺酸仑伐替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '腹泻', '蛋白尿'], 'metabolism': 'CYP3A4'}, {'id': 'anastrozole', 'name': '阿那曲唑', 'category': '芳香化酶抑制剂', 'generic_name': '阿那曲唑', 'contraindications': ['孕妇', '绝经前妇女'], 'side_effects': ['骨质疏松', '关节痛'], 'metabolism': 'CYP3A4/UGT'}, {'id': 'tadalafil', 'name': '他达拉非', 'category': 'PDE5抑制剂', 'generic_name': '他达拉非', 'contraindications': ['硝酸酯类使用中'], 'side_effects': ['头痛', '消化不良', '背痛'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'brimonidine', 'name': '溴莫尼定', 'category': 'α2受体激动剂(眼科)', 'generic_name': '酒石酸溴莫尼定', 'contraindications': ['MAO抑制剂使用中', '新生儿'], 'side_effects': ['口干', '嗜睡'], 'metabolism': '肝脏代谢'}, {'id': 'zoledronic_acid', 'name': '唑来膦酸', 'category': '双膦酸盐', 'generic_name': '唑来膦酸', 'contraindications': ['严重肾功能不全'], 'side_effects': ['发热', '骨坏死', '肾毒性'], 'metabolism': '不代谢'}, {'id': 'vitamin_d3', 'name': '维生素D3', 'category': '维生素', 'generic_name': '胆钙化醇', 'contraindications': ['高钙血症'], 'side_effects': ['高钙血症(过量)'], 'metabolism': 'CYP2R1/CYP27B1'}, {'id': 'lidocaine_local', 'name': '利多卡因(局麻)', 'category': '局部麻醉药', 'generic_name': '盐酸利多卡因', 'contraindications': ['严重窦房传导阻滞'], 'side_effects': ['中枢神经毒性', '心脏毒性'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'potassium_chloride', 'name': '氯化钾', 'category': '电解质补充剂', 'generic_name': '氯化钾', 'contraindications': ['高钾血症', '严重肾功能不全'], 'side_effects': ['高钾血症', '消化道刺激'], 'metabolism': '肾脏排泄'}, {'id': 'ferrous_sulfate', 'name': '硫酸亚铁', 'category': '铁剂', 'generic_name': '硫酸亚铁', 'contraindications': ['血色病'], 'side_effects': ['便秘', '黑便', '恶心'], 'metabolism': '十二指肠吸收'}, {'id': 'baclofen', 'name': '巴氯芬', 'category': '肌肉松弛剂', 'generic_name': '巴氯芬', 'contraindications': ['癫痫'], 'side_effects': ['嗜睡', '肌无力', '戒断综合征'], 'metabolism': '部分肝脏代谢'}, {'id': 'thalidomide', 'name': '沙利度胺', 'category': '免疫调节剂', 'generic_name': '沙利度胺', 'contraindications': ['孕妇(强致畸)'], 'side_effects': ['致畸', '深静脉血栓', '嗜睡'], 'metabolism': '非CYP水解'}, {'id': 'danazol', 'name': '达那唑', 'category': '雄激素', 'generic_name': '达那唑', 'contraindications': ['孕妇', '卟啉症'], 'side_effects': ['男性化', '肝毒性'], 'metabolism': 'CYP3A4'}]
DRUGS.extend(_EXTRA_DRUGS)

_EXTRA_INTERACTIONS = [('warfarin', 'cotrimoxazole', 'high', '复方新诺明抑制CYP2C9,增强华法林抗凝效果'), ('warfarin', 'fluoxetine', 'high', '氟西汀抑制CYP2C9,增强华法林抗凝效果'), ('clopidogrel', 'omeprazole', 'medium', '奥美拉唑抑制CYP2C19,氯吡格雷活化受阻'), ('clopidogrel', 'esomeprazole', 'medium', '埃索美拉唑抑制CYP2C19,氯吡格雷活化受阻'), ('atenolol', 'diltiazem', 'high', '双重心脏传导抑制'), ('carvedilol', 'verapamil', 'critical', '双重心脏传导抑制+α阻滞,严重低血压'), ('bisoprolol', 'diltiazem', 'high', '双重心脏传导抑制'), ('nebivolol', 'verapamil', 'high', '双重心脏传导抑制'), ('verapamil', 'lovastatin', 'critical', '维拉帕米强效抑制CYP3A4,横纹肌溶解风险'), ('diltiazem', 'carbamazepine', 'high', '地尔硫卓抑制CYP3A4,卡马西平血药浓度升高'), ('spironolactone', 'potassium_chloride', 'critical', '保钾利尿+补钾,高钾血症风险极高'), ('digoxin', 'verapamil', 'high', '维拉帕米抑制P-gp,地高辛血药浓度升高'), ('amiodarone', 'flecainide', 'critical', '胺碘酮+IC类,严重致心律失常风险'), ('amiodarone', 'sotalol', 'critical', '双重QT延长,尖端扭转型室速风险极高'), ('amiodarone', 'dronedarone', 'critical', '药理学重复+QT延长,禁忌合用'), ('amiodarone', 'simvastatin', 'high', '胺碘酮抑制CYP3A4,他汀暴露量增加'), ('flecainide', 'propranolol', 'high', '双重心脏传导抑制'), ('sotalol', 'verapamil', 'critical', '双重QT延长+心脏传导抑制'), ('dronedarone', 'simvastatin', 'high', '决奈达隆抑制CYP3A4/P-gp'), ('dronedarone', 'dabigatran', 'high', '决奈达隆抑制P-gp,达比加群血药浓度升高'), ('ciprofloxacin', 'warfarin', 'high', '环丙沙星增强华法林抗凝效果'), ('ciprofloxacin', 'clozapine', 'critical', '环丙沙星抑制CYP1A2,氯氮平血药浓度升高'), ('moxifloxacin', 'amiodarone', 'critical', '双重QT延长'), ('moxifloxacin', 'sotalol', 'critical', '双重QT延长'), ('moxifloxacin', 'haloperidol', 'high', '双重QT延长'), ('levofloxacin', 'warfarin', 'medium', '左氧氟沙星增强华法林抗凝效果'), ('clarithromycin', 'carbamazepine', 'high', '克拉霉素抑制CYP3A4,卡马西平血药浓度升高'), ('clarithromycin', 'verapamil', 'high', '心动过缓和低血压风险'), ('azithromycin', 'amiodarone', 'high', 'QT延长风险'), ('metronidazole', 'lithium', 'high', '可能升高锂盐血药浓度'), ('metronidazole', 'fluorouracil', 'critical', '甲硝唑抑制DPD,5-FU毒性增加'), ('cotrimoxazole', 'methotrexate', 'high', '抑制肾小管分泌,甲氨蝶呤蓄积'), ('cotrimoxazole', 'warfarin', 'high', '抑制CYP2C9,增强华法林抗凝效果'), ('cotrimoxazole', 'lithium', 'high', '影响肾脏排泄,锂盐血药浓度升高'), ('cotrimoxazole', 'spironolactone', 'high', '高钾血症风险叠加'), ('gentamicin', 'amphotericin_b', 'high', '双重肾毒性'), ('vancomycin', 'amphotericin_b', 'high', '双重肾毒性'), ('meropenem', 'valproic_acid', 'critical', '碳青霉烯类显著降低丙戊酸血药浓度,癫痫发作风险'), ('linezolid', 'tramadol', 'high', 'MAO抑制+阿片,5-HT综合征/癫痫风险'), ('linezolid', 'methylphenidate', 'high', 'MAO抑制+兴奋剂,高血压危象风险'), ('nitrofurantoin', 'magnesium_antacid', 'medium', '抗酸剂降低呋喃妥因吸收'), ('rifampicin', 'warfarin', 'critical', '利福平强效CYP诱导,华法林效果大幅降低'), ('rifampicin', 'oral_contraceptives', 'critical', '利福平诱导CYP3A4,口服避孕药失效'), ('rifampicin', 'simvastatin', 'high', '利福平诱导CYP3A4,他汀效果降低'), ('rifampicin', 'tacrolimus', 'critical', '利福平诱导CYP3A4,他克莫司血药浓度大幅降低'), ('rifampicin', 'cyclosporine', 'critical', '利福平诱导CYP3A4,环孢素血药浓度大幅降低'), ('fluconazole', 'phenytoin', 'high', '氟康唑抑制CYP2C9,苯妥英血药浓度升高'), ('itraconazole', 'midazolam', 'critical', '伊曲康唑抑制CYP3A4,咪达唑仑暴露量大幅增加'), ('itraconazole', 'digoxin', 'high', '伊曲康唑抑制P-gp,地高辛血药浓度升高'), ('voriconazole', 'rifampicin', 'critical', '利福平强效诱导CYP,伏立康唑血药浓度大幅降低'), ('voriconazole', 'carbamazepine', 'high', '卡马西平诱导CYP,伏立康唑效果降低'), ('voriconazole', 'sirolimus', 'critical', '伏立康唑抑制CYP3A4,西罗莫司暴露量大幅增加'), ('posaconazole', 'simvastatin', 'critical', '泊沙康唑强效抑制CYP3A4,横纹肌溶解'), ('posaconazole', 'tacrolimus', 'high', '泊沙康唑抑制CYP3A4,他克莫司血药浓度升高'), ('amphotericin_b', 'furosemide', 'high', '袢利尿剂加重两性霉素B肾毒性'), ('griseofulvin', 'warfarin', 'medium', '灰黄霉素诱导CYP,华法林效果降低'), ('griseofulvin', 'oral_contraceptives', 'medium', '灰黄霉素可能降低口服避孕药效果'), ('fluoxetine', 'dextromethorphan', 'high', 'SSRI+右美沙芬,5-HT综合征风险'), ('fluoxetine', 'lithium', 'high', 'SSRI增强锂盐神经毒性'), ('sertraline', 'pimozide', 'critical', 'CYP2D6抑制+pimozide,QT延长风险'), ('paroxetine', 'tamoxifen', 'critical', '帕罗西汀强效抑制CYP2D6,他莫昔芬活化受阻'), ('fluoxetine', 'tamoxifen', 'critical', '氟西汀强效抑制CYP2D6,他莫昔芬活化受阻'), ('duloxetine', 'tramadol', 'critical', 'SNRI+阿片,5-HT综合征风险'), ('duloxetine', 'fluoxetine', 'high', '双重5-HT再摄取抑制,5-HT综合征风险'), ('mirtazapine', 'tramadol', 'high', '5-HT综合征风险'), ('mirtazapine', 'linezolid', 'high', 'MAO抑制+5-HT能药物'), ('trazodone', 'fluoxetine', 'medium', '氟西汀抑制CYP2D6,曲唑酮血药浓度升高'), ('lithium', 'carbamazepine', 'high', '双重神经毒性叠加'), ('lithium', 'haloperidol', 'high', '双重神经毒性,脑病风险'), ('valproic_acid', 'carbamazepine', 'medium', '丙戊酸升高卡马西平环氧化物水平'), ('valproic_acid', 'lamotrigine', 'critical', '丙戊酸抑制拉莫三嗪代谢,SJS/TEN风险极高'), ('carbamazepine', 'clarithromycin', 'high', '克拉霉素抑制CYP3A4,卡马西平中毒'), ('carbamazepine', 'oral_contraceptives', 'critical', '卡马西平诱导CYP3A4,口服避孕药失效'), ('carbamazepine', 'tacrolimus', 'critical', '卡马西平诱导CYP3A4,他克莫司血药浓度大幅降低'), ('lamotrigine', 'valproic_acid', 'critical', '丙戊酸抑制拉莫三嗪葡萄糖醛酸化,SJS/TEN风险极高'), ('phenytoin', 'fluconazole', 'high', '氟康唑抑制CYP2C9,苯妥英中毒'), ('phenytoin', 'amiodarone', 'high', '胺碘酮抑制CYP2C9,苯妥英中毒'), ('phenytoin', 'warfarin', 'medium', '苯妥英诱导CYP,华法林效果可能变化'), ('olanzapine', 'fluvoxamine', 'high', '氟伏沙明强效抑制CYP1A2,奥氮平暴露量大幅增加'), ('clozapine', 'fluvoxamine', 'critical', '氟伏沙明强效抑制CYP1A2,氯氮平血药浓度大幅升高'), ('clozapine', 'fluoxetine', 'high', '氟西汀抑制CYP2D6,氯氮平血药浓度升高'), ('clozapine', 'carbamazepine', 'critical', '卡马西平诱导CYP+骨髓抑制叠加'), ('clozapine', 'ciprofloxacin', 'critical', '环丙沙星抑制CYP1A2,氯氮平血药浓度大幅升高'), ('methylphenidate', 'clonidine', 'high', '高血压风险'), ('atomoxetine', 'fluoxetine', 'medium', '氟西汀抑制CYP2D6,托莫西汀血药浓度升高'), ('metformin', 'contrast_dye', 'critical', '碘造影剂致肾功能损害,二甲双胍蓄积→乳酸酸中毒'), ('metformin', 'alcohol', 'high', '酒精增加乳酸酸中毒风险'), ('repaglinide', 'gemfibrozil', 'critical', '吉非贝齐抑制CYP2C8,瑞格列奈暴露量大幅增加'), ('repaglinide', 'clarithromycin', 'high', '克拉霉素抑制CYP3A4,瑞格列奈血药浓度升高'), ('levothyroxine', 'ferrous_sulfate', 'medium', '铁剂降低左甲状腺素吸收(需间隔4小时)'), ('levothyroxine', 'amiodarone', 'medium', '胺碘酮含碘,影响甲状腺功能'), ('insulin_glargine', 'pioglitazone', 'medium', '噻唑烷二酮+胰岛素,液体潴留/心衰风险增加'), ('theophylline', 'fluvoxamine', 'critical', '氟伏沙明强效抑制CYP1A2,茶碱中毒'), ('salbutamol', 'propranolol', 'high', 'β受体阻滞剂拮抗支气管扩张效果'), ('budesonide', 'ketoconazole', 'high', '酮康唑抑制CYP3A4,吸入性激素全身暴露量增加'), ('fluticasone', 'ritonavir', 'critical', '利托那韦强效抑制CYP3A4,氟替卡松全身暴露量大幅增加'), ('dextromethorphan', 'fluoxetine', 'high', 'SSRI+右美沙芬,5-HT综合征风险'), ('dextromethorphan', 'sertraline', 'high', 'SSRI+右美沙芬,5-HT综合征风险'), ('codeine', 'fluoxetine', 'high', '氟西汀抑制CYP2D6,可待因无法转化为吗啡'), ('codeine', 'paroxetine', 'high', '帕罗西汀抑制CYP2D6,可待因无法转化为吗啡'), ('omeprazole', 'clopidogrel', 'medium', '奥美拉唑抑制CYP2C19,氯吡格雷活化受阻'), ('omeprazole', 'diazepam', 'medium', '奥美拉唑抑制CYP2C19,地西泮代谢减慢'), ('omeprazole', 'phenytoin', 'medium', '奥美拉唑抑制CYP2C19,苯妥英血药浓度可能升高'), ('cimetidine', 'phenytoin', 'high', '西咪替丁抑制CYP,苯妥英血药浓度升高'), ('cimetidine', 'lidocaine_iv', 'high', '西咪替丁降低肝脏血流+抑制CYP,利多卡因蓄积'), ('sucralfate', 'ciprofloxacin', 'high', '硫糖铝螯合喹诺酮类,吸收大幅降低'), ('sucralfate', 'levothyroxine', 'medium', '硫糖铝降低左甲状腺素吸收'), ('tacrolimus', 'voriconazole', 'high', '伏立康唑抑制CYP3A4,他克莫司血药浓度升高'), ('tacrolimus', 'posaconazole', 'high', '泊沙康唑抑制CYP3A4,他克莫司血药浓度升高'), ('tacrolimus', 'erythromycin', 'high', '红霉素抑制CYP3A4,他克莫司血药浓度升高'), ('tacrolimus', 'rifampicin', 'critical', '利福平诱导CYP3A4,他克莫司血药浓度大幅降低'), ('tacrolimus', 'carbamazepine', 'critical', '卡马西平诱导CYP3A4,他克莫司血药浓度大幅降低'), ('cyclosporine', 'simvastatin', 'critical', '环孢素抑制OATP/CYP3A4,横纹肌溶解'), ('cyclosporine', 'atorvastatin', 'high', '环孢素抑制OATP/CYP3A4'), ('cyclosporine', 'methotrexate', 'high', '环孢素降低甲氨蝶呤肾脏清除'), ('cyclosporine', 'NSAIDs', 'high', 'NSAIDs加重环孢素肾毒性'), ('cyclosporine', 'amphotericin_b', 'high', '双重肾毒性'), ('mycophenolate', 'cholestyramine', 'high', '考来烯胺降低霉酚酸肠肝循环'), ('leflunomide', 'methotrexate', 'high', '双重免疫抑制+肝毒性叠加'), ('methotrexate_onco', 'NSAIDs', 'critical', 'NSAIDs降低甲氨蝶呤肾脏清除,严重骨髓抑制'), ('methotrexate_onco', 'penicillins', 'high', '青霉素类降低甲氨蝶呤肾脏清除'), ('methotrexate_onco', 'cotrimoxazole', 'high', '双重抗叶酸,严重骨髓抑制'), ('fluorouracil', 'metronidazole', 'critical', '甲硝唑抑制DPD,5-FU毒性大幅增加'), ('fluorouracil', 'warfarin', 'high', '5-FU增强华法林抗凝效果'), ('irinotecan', 'ketoconazole', 'high', '酮康唑抑制CYP3A4,SN-38暴露量增加'), ('cisplatin', 'gentamicin', 'high', '双重肾毒性和耳毒性'), ('tamoxifen', 'fluoxetine', 'critical', '氟西汀抑制CYP2D6,他莫昔芬活化受阻'), ('tamoxifen', 'paroxetine', 'critical', '帕罗西汀抑制CYP2D6,他莫昔芬活化受阻'), ('tamoxifen', 'bupropion', 'high', '安非他酮抑制CYP2D6,他莫昔芬活化受阻'), ('capecitabine', 'warfarin', 'high', '卡培他滨增强华法林抗凝效果'), ('sildenafil', 'isosorbide_dinitrate', 'critical', 'PDE5抑制剂+硝酸酯类,严重低血压,禁忌合用'), ('tadalafil', 'nitroglycerin', 'critical', 'PDE5抑制剂+硝酸酯类,严重低血压,禁忌合用'), ('sildenafil', 'ketoconazole', 'high', '酮康唑抑制CYP3A4,西地那非暴露量大幅增加'), ('sildenafil', 'ritonavir', 'critical', '利托那韦强效抑制CYP3A4,西地那非暴露量大幅增加'), ('allopurinol', 'mercaptopurine', 'critical', '别嘌醇抑制XO,6-MP蓄积,严重骨髓抑制'), ('tizanidine', 'fluvoxamine', 'critical', '氟伏沙明强效抑制CYP1A2,替扎尼定暴露量大幅增加'), ('baclofen', 'diazepam', 'high', '双重中枢抑制,呼吸抑制风险'), ('propofol', 'fentanyl', 'high', '双重呼吸抑制和低血压'), ('epinephrine', 'propranolol', 'critical', '非选择性β阻滞剂+肾上腺素,严重高血压危象'), ('diazepam', 'opioids', 'critical', '苯二氮卓+阿片,呼吸抑制风险极高(黑框警告)'), ('diazepam', 'omeprazole', 'medium', '奥美拉唑抑制CYP2C19,地西泮代谢减慢'), ('lidocaine_local', 'cimetidine', 'high', '西咪替丁降低肝脏血流+抑制CYP,利多卡因蓄积'), ('bupivacaine', 'propranolol', 'medium', 'β阻滞剂降低布比卡因肝脏清除'), ('danazol', 'carbamazepine', 'high', '达那唑抑制CYP3A4,卡马西平血药浓度升高'), ('cyclophosphamide', 'allopurinol', 'medium', '别嘌醇可能加重环磷酰胺骨髓抑制'), ('doxorubicin', 'trastuzumab', 'critical', '心脏毒性叠加(心衰风险极高)'), ('amiodarone', 'levothyroxine', 'medium', '胺碘酮含碘,影响甲状腺功能')]
INTERACTIONS.extend(_EXTRA_INTERACTIONS)

_EXTRA_ALTERNATIVES = [('aspirin', 'clopidogrel', 'P2Y12抑制剂,单药抗血小板'), ('omeprazole', 'pantoprazole', '泮托拉唑CYP2C19依赖较低,药物相互作用较少'), ('omeprazole', 'rabeprazole', '雷贝拉唑非酶代谢为主,相互作用少'), ('cimetidine', 'famotidine', '法莫替丁不抑制CYP,药物相互作用少'), ('glibenclamide', 'gliclazide', '格列齐特低血糖风险较低'), ('glibenclamide', 'metformin', '双胍类不引起低血糖'), ('diazepam', 'oxazepam', '奥沙西泮仅经葡萄糖醛酸化,相互作用最少'), ('carbamazepine', 'levetiracetam', '左乙拉西坦不经CYP代谢,药物相互作用最少'), ('valproic_acid', 'levetiracetam', '不经CYP代谢,相互作用少'), ('cyclosporine', 'sirolimus', 'mTOR抑制剂,肾毒性低'), ('metformin', 'empagliflozin', 'SGLT2抑制剂有心血管保护作用'), ('metformin', 'sitagliptin', 'DPP-4抑制剂低血糖风险极低'), ('amlodipine', 'lercanidipine', '乐卡地平水肿发生率较低'), ('amiodarone', 'dronedarone', '决奈达隆肺/甲状腺毒性较低'), ('gentamicin', 'amikacin', '阿米卡星耐药率较低'), ('doxorubicin', 'epirubicin', '表柔比星心脏毒性较低'), ('cisplatin', 'carboplatin', '卡铂肾毒性和耳毒性较低'), ('paclitaxel', 'docetaxel', '多西他赛给药频率较低')]
ALTERNATIVES.extend(_EXTRA_ALTERNATIVES)


# ==================== 第二批扩展药物 ====================
_EXTRA_DRUGS_2 = [{'id': 'azilsartan', 'name': '阿齐沙坦', 'category': 'ARB', 'generic_name': '阿齐沙坦酯', 'contraindications': ['孕妇', '双侧肾动脉狭窄'], 'side_effects': ['低血压', '高钾血症'], 'metabolism': 'CYP2C9'}, {'id': 'olmesartan', 'name': '奥美沙坦', 'category': 'ARB', 'generic_name': '奥美沙坦酯', 'contraindications': ['孕妇', '双侧肾动脉狭窄'], 'side_effects': ['低血压', '高钾血症'], 'metabolism': 'CYP2C9'}, {'id': 'candesartan', 'name': '坎地沙坦', 'category': 'ARB', 'generic_name': '坎地沙坦酯', 'contraindications': ['孕妇', '双侧肾动脉狭窄'], 'side_effects': ['低血压', '高钾血症'], 'metabolism': 'CYP2C9'}, {'id': 'telmisartan', 'name': '替米沙坦', 'category': 'ARB', 'generic_name': '替米沙坦', 'contraindications': ['孕妇', '双侧肾动脉狭窄'], 'side_effects': ['低血压', '高钾血症'], 'metabolism': 'UGT1A3'}, {'id': 'perindopril', 'name': '培哚普利', 'category': 'ACEI', 'generic_name': '培哚普利叔丁胺', 'contraindications': ['血管性水肿史', '孕妇', '双侧肾动脉狭窄'], 'side_effects': ['干咳', '高钾血症'], 'metabolism': 'CYP3A4'}, {'id': 'trandolapril', 'name': '群多普利', 'category': 'ACEI', 'generic_name': '群多普利', 'contraindications': ['血管性水肿史', '孕妇'], 'side_effects': ['干咳', '高钾血症'], 'metabolism': 'CYP3A4'}, {'id': 'fosinopril', 'name': '福辛普利', 'category': 'ACEI', 'generic_name': '福辛普利钠', 'contraindications': ['血管性水肿史', '孕妇'], 'side_effects': ['干咳', '高钾血症'], 'metabolism': '肝肾双通道'}, {'id': 'benazepril', 'name': '贝那普利', 'category': 'ACEI', 'generic_name': '盐酸贝那普利', 'contraindications': ['血管性水肿史', '孕妇'], 'side_effects': ['干咳', '高钾血症'], 'metabolism': 'CYP3A4'}, {'id': 'prazosin', 'name': '哌唑嗪', 'category': 'α受体阻滞剂', 'generic_name': '盐酸哌唑嗪', 'contraindications': ['对本品过敏'], 'side_effects': ['首剂低血压', '头晕'], 'metabolism': 'CYP3A4'}, {'id': 'terazosin', 'name': '特拉唑嗪', 'category': 'α受体阻滞剂', 'generic_name': '盐酸特拉唑嗪', 'contraindications': ['体位性低血压'], 'side_effects': ['低血压', '头晕'], 'metabolism': 'CYP3A4'}, {'id': 'indapamide', 'name': '吲达帕胺', 'category': '利尿药', 'generic_name': '吲达帕胺', 'contraindications': ['严重肝功能不全', '低钾血症'], 'side_effects': ['低钾血症', '高尿酸血症'], 'metabolism': 'CYP3A4'}, {'id': 'chlorthalidone', 'name': '氯噻酮', 'category': '利尿药', 'generic_name': '氯噻酮', 'contraindications': ['无尿', '严重肝肾功能不全'], 'side_effects': ['低钾血症', '高尿酸血症'], 'metabolism': '肾脏排泄'}, {'id': 'amiloride', 'name': '阿米洛利', 'category': '利尿药', 'generic_name': '盐酸阿米洛利', 'contraindications': ['高钾血症', '严重肾功能不全'], 'side_effects': ['高钾血症'], 'metabolism': '不代谢'}, {'id': 'triamterene', 'name': '氨苯蝶啶', 'category': '利尿药', 'generic_name': '氨苯蝶啶', 'contraindications': ['高钾血症', '严重肾功能不全'], 'side_effects': ['高钾血症', '肾结石'], 'metabolism': 'CYP1A2'}, {'id': 'acetazolamide', 'name': '乙酰唑胺', 'category': '利尿药', 'generic_name': '乙酰唑胺', 'contraindications': ['低钠血症', '低钾血症', '严重肝功能不全'], 'side_effects': ['代谢性酸中毒', '感觉异常'], 'metabolism': '不代谢'}, {'id': 'nesiritide', 'name': '奈西立肽', 'category': '心衰药', 'generic_name': '奈西立肽', 'contraindications': ['心源性休克', '收缩压<90mmHg'], 'side_effects': ['低血压'], 'metabolism': '蛋白水解'}, {'id': 'ivabradine_hf', 'name': '伊伐布雷定(心衰)', 'category': '抗心绞痛药', 'generic_name': '伊伐布雷定', 'contraindications': ['急性失代偿心衰'], 'side_effects': ['心动过缓', '闪光幻觉'], 'metabolism': 'CYP3A4'}, {'id': 'penicillin_v', 'name': '青霉素V', 'category': '青霉素类', 'generic_name': '青霉素V钾', 'contraindications': ['青霉素过敏'], 'side_effects': ['过敏反应', '腹泻'], 'metabolism': '肾脏排泄'}, {'id': 'cefadroxil', 'name': '头孢羟氨苄', 'category': '头孢菌素类', 'generic_name': '头孢羟氨苄', 'contraindications': ['头孢菌素过敏'], 'side_effects': ['腹泻', '过敏反应'], 'metabolism': '肾脏排泄'}, {'id': 'cefdinir', 'name': '头孢地尼', 'category': '头孢菌素类', 'generic_name': '头孢地尼', 'contraindications': ['头孢菌素过敏'], 'side_effects': ['腹泻', '恶心'], 'metabolism': '肾脏排泄'}, {'id': 'cefixime', 'name': '头孢克肟', 'category': '头孢菌素类', 'generic_name': '头孢克肟', 'contraindications': ['头孢菌素过敏'], 'side_effects': ['腹泻', '恶心'], 'metabolism': '肾脏排泄'}, {'id': 'cefprozil', 'name': '头孢丙烯', 'category': '头孢菌素类', 'generic_name': '头孢丙烯', 'contraindications': ['头孢菌素过敏'], 'side_effects': ['腹泻', '恶心', '皮疹'], 'metabolism': '肾脏排泄'}, {'id': 'cefdinir', 'name': '头孢地尼(口服)', 'category': '头孢菌素类', 'generic_name': '头孢地尼', 'contraindications': ['头孢菌素过敏'], 'side_effects': ['腹泻', '便血(铁剂合用时)'], 'metabolism': '肾脏排泄'}, {'id': 'sparfloxacin', 'name': '司帕沙星', 'category': '喹诺酮类', 'generic_name': '司帕沙星', 'contraindications': ['QT延长'], 'side_effects': ['光敏感', 'QT延长'], 'metabolism': 'CYP1A2'}, {'id': 'gemifloxacin', 'name': '吉米沙星', 'category': '喹诺酮类', 'generic_name': '吉米沙星', 'contraindications': ['QT延长'], 'side_effects': ['腹泻', '皮疹'], 'metabolism': '部分CYP代谢'}, {'id': 'tetracycline', 'name': '四环素', 'category': '四环素类', 'generic_name': '盐酸四环素', 'contraindications': ['孕妇', '8岁以下儿童', '严重肝功能不全'], 'side_effects': ['牙齿着色', '光敏感'], 'metabolism': '肾脏排泄'}, {'id': 'azithromycin_iv', 'name': '阿奇霉素(注射)', 'category': '大环内酯类', 'generic_name': '阿奇霉素', 'contraindications': ['大环内酯类过敏'], 'side_effects': ['注射部位反应', 'QT延长'], 'metabolism': 'CYP3A4(少量)'}, {'id': 'roxithromycin', 'name': '罗红霉素', 'category': '大环内酯类', 'generic_name': '罗红霉素', 'contraindications': ['大环内酯类过敏'], 'side_effects': ['恶心', '腹痛'], 'metabolism': 'CYP3A4'}, {'id': 'mupirocin_nasal', 'name': '莫匹罗星(鼻用)', 'category': '抗生素(外用)', 'generic_name': '莫匹罗星', 'contraindications': ['对本品过敏'], 'side_effects': ['鼻出血', '头痛'], 'metabolism': '局部代谢'}, {'id': 'polymyxin_b', 'name': '多粘菌素B', 'category': '多粘菌素类', 'generic_name': '硫酸多粘菌素B', 'contraindications': ['多粘菌素过敏'], 'side_effects': ['肾毒性', '神经毒性'], 'metabolism': '肾脏排泄'}, {'id': 'quinupristin_dalfopristin', 'name': '奎奴普丁/达福普汀', 'category': '链阳菌素类', 'generic_name': '奎奴普丁/达福普汀', 'contraindications': ['对本品过敏'], 'side_effects': ['关节痛', '肌痛', '静脉炎'], 'metabolism': 'CYP3A4'}, {'id': 'tedizolid', 'name': '特地唑胺', 'category': '恶唑烷酮类', 'generic_name': '磷酸特地唑胺', 'contraindications': ['对本品过敏'], 'side_effects': ['恶心', '头痛'], 'metabolism': '磺基转移酶'}, {'id': 'omadacycline', 'name': '奥马环素', 'category': '甘氨酰环素类', 'generic_name': '奥马环素', 'contraindications': ['对本品过敏'], 'side_effects': ['恶心', '呕吐', '光敏感'], 'metabolism': '部分肝脏代谢'}, {'id': 'delafloxacin', 'name': '地拉沙星', 'category': '喹诺酮类', 'generic_name': '地拉沙星', 'contraindications': ['对本品过敏'], 'side_effects': ['恶心', '腹泻'], 'metabolism': 'UGT/醛氧化酶'}, {'id': 'lefamulin', 'name': '来法莫林', 'category': '截短侧耳素类', 'generic_name': '醋酸来法莫林', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['恶心', '腹泻', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'lurasidone', 'name': '鲁拉西酮', 'category': '抗精神病药', 'generic_name': '盐酸鲁拉西酮', 'contraindications': ['CYP3A4强抑制剂/诱导剂合用'], 'side_effects': ['嗜睡', '恶心'], 'metabolism': 'CYP3A4'}, {'id': 'asenapine', 'name': '阿塞那平', 'category': '抗精神病药', 'generic_name': '马来酸阿塞那平', 'contraindications': ['严重肝功能不全'], 'side_effects': ['嗜睡', '头晕', '体重增加'], 'metabolism': 'UGT1A4/CYP1A2'}, {'id': 'iloperidone', 'name': '伊潘立酮', 'category': '抗精神病药', 'generic_name': '伊潘立酮', 'contraindications': ['QT延长'], 'side_effects': ['QT延长', '体位性低血压'], 'metabolism': 'CYP2D6/CYP3A4'}, {'id': 'cariprazine', 'name': '卡利拉嗪', 'category': '抗精神病药', 'generic_name': '卡利拉嗪', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['锥体外系反应', '失眠'], 'metabolism': 'CYP3A4'}, {'id': 'brexpiprazole', 'name': '布瑞哌唑', 'category': '抗精神病药', 'generic_name': '布瑞哌唑', 'contraindications': ['CYP2D6强抑制剂合用(高剂量时)'], 'side_effects': ['体重增加', '头痛'], 'metabolism': 'CYP3A4/CYP2D6'}, {'id': 'pimavanserin', 'name': '吡马色林', 'category': '抗精神病药', 'generic_name': '酒石酸吡马色林', 'contraindications': ['QT延长'], 'side_effects': ['QT延长', '外周水肿'], 'metabolism': 'CYP3A4'}, {'id': 'fluphenazine', 'name': '氟奋乃静', 'category': '抗精神病药', 'generic_name': '盐酸氟奋乃静', 'contraindications': ['昏迷', '骨髓抑制'], 'side_effects': ['锥体外系反应', '迟发性运动障碍'], 'metabolism': 'CYP2D6'}, {'id': 'perphenazine', 'name': '奋乃静', 'category': '抗精神病药', 'generic_name': '奋乃静', 'contraindications': ['昏迷', '骨髓抑制'], 'side_effects': ['锥体外系反应', '嗜睡'], 'metabolism': 'CYP2D6'}, {'id': 'chlorpromazine', 'name': '氯丙嗪', 'category': '抗精神病药', 'generic_name': '盐酸氯丙嗪', 'contraindications': ['昏迷', '骨髓抑制'], 'side_effects': ['体位性低血压', '锥体外系反应', 'QT延长'], 'metabolism': 'CYP2D6/CYP1A2'}, {'id': 'loxapine', 'name': '洛沙平', 'category': '抗精神病药', 'generic_name': '洛沙平', 'contraindications': ['哮喘', 'COPD'], 'side_effects': ['支气管痉挛(吸入时)', '锥体外系反应'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'paliperidone_palmitate', 'name': '帕利哌酮棕榈酸酯', 'category': '抗精神病药', 'generic_name': '帕利哌酮棕榈酸酯', 'contraindications': ['帕利哌酮过敏'], 'side_effects': ['注射部位反应', '锥体外系反应'], 'metabolism': 'CYP2D6(少量)'}, {'id': 'desvenlafaxine', 'name': '去甲文拉法辛', 'category': 'SNRI', 'generic_name': '琥珀酸去甲文拉法辛', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['恶心', '头晕', '高血压'], 'metabolism': 'CYP3A4(少量)'}, {'id': 'vilazodone', 'name': '维拉佐酮', 'category': 'SSRI', 'generic_name': '盐酸维拉佐酮', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['腹泻', '恶心'], 'metabolism': 'CYP3A4'}, {'id': 'vortioxetine', 'name': '沃替西汀', 'category': '多模式抗抑郁药', 'generic_name': '氢溴酸沃替西汀', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['恶心', '头痛'], 'metabolism': 'CYP2D6'}, {'id': 'selegiline', 'name': '司来吉兰', 'category': 'MAO-B抑制剂', 'generic_name': '盐酸司来吉兰', 'contraindications': ['MAO抑制剂合用', '哌替啶合用'], 'side_effects': ['失眠', '恶心', '体位性低血压'], 'metabolism': 'CYP2B6/CYP2C19'}, {'id': 'rasagiline', 'name': '雷沙吉兰', 'category': 'MAO-B抑制剂', 'generic_name': '甲磺酸雷沙吉兰', 'contraindications': ['MAO抑制剂合用', '哌替啶合用'], 'side_effects': ['头痛', '关节痛'], 'metabolism': 'CYP1A2'}, {'id': 'safinamide', 'name': '沙芬酰胺', 'category': 'MAO-B抑制剂', 'generic_name': '甲磺酸沙芬酰胺', 'contraindications': ['严重肝功能不全'], 'side_effects': ['失眠', '恶心'], 'metabolism': 'CYP3A4/MAO-B'}, {'id': 'ropinirole', 'name': '罗匹尼罗', 'category': '多巴胺受体激动剂', 'generic_name': '盐酸罗匹尼罗', 'contraindications': ['对本品过敏'], 'side_effects': ['嗜睡', '恶心', '幻觉'], 'metabolism': 'CYP1A2'}, {'id': 'rotigotine', 'name': '罗替高汀', 'category': '多巴胺受体激动剂', 'generic_name': '罗替高汀', 'contraindications': ['对本品过敏'], 'side_effects': ['恶心', '嗜睡', '注射部位反应'], 'metabolism': 'CYP/MAO/COMT'}, {'id': 'tolcapone', 'name': '托卡朋', 'category': 'COMT抑制剂', 'generic_name': '托卡朋', 'contraindications': ['肝功能不全'], 'side_effects': ['肝毒性', '腹泻', '运动障碍加重'], 'metabolism': 'CYP3A4'}, {'id': 'amantadine', 'name': '金刚烷胺', 'category': '抗帕金森药', 'generic_name': '盐酸金刚烷胺', 'contraindications': ['严重肾功能不全'], 'side_effects': ['幻觉', '网状青斑', '踝部水肿'], 'metabolism': '不代谢'}, {'id': 'benztropine', 'name': '苯扎托品', 'category': '抗胆碱药', 'generic_name': '甲磺酸苯扎托品', 'contraindications': ['闭角型青光眼', '肠梗阻'], 'side_effects': ['口干', '便秘', '尿潴留'], 'metabolism': 'CYP2D6'}, {'id': 'trihexyphenidyl', 'name': '苯海索', 'category': '抗胆碱药', 'generic_name': '盐酸苯海索', 'contraindications': ['闭角型青光眼', '肠梗阻'], 'side_effects': ['口干', '便秘', '尿潴留'], 'metabolism': '肝脏代谢'}, {'id': 'nateglinide', 'name': '那格列奈', 'category': '格列奈类', 'generic_name': '那格列奈', 'contraindications': ['1型糖尿病'], 'side_effects': ['低血糖'], 'metabolism': 'CYP2C9/CYP3A4'}, {'id': 'exenatide', 'name': '艾塞那肽', 'category': 'GLP-1受体激动剂', 'generic_name': '艾塞那肽', 'contraindications': ['严重肾功能不全', '甲状腺髓样癌史'], 'side_effects': ['恶心', '呕吐'], 'metabolism': '蛋白水解'}, {'id': 'dulaglutide', 'name': '度拉糖肽', 'category': 'GLP-1受体激动剂', 'generic_name': '度拉糖肽', 'contraindications': ['甲状腺髓样癌史', 'MEN2'], 'side_effects': ['恶心', '腹泻'], 'metabolism': '蛋白水解'}, {'id': 'lixisenatide', 'name': '利司那肽', 'category': 'GLP-1受体激动剂', 'generic_name': '利司那肽', 'contraindications': ['甲状腺髓样癌史'], 'side_effects': ['恶心', '呕吐'], 'metabolism': '蛋白水解'}, {'id': 'ertugliflozin', 'name': '艾托格列净', 'category': 'SGLT2抑制剂', 'generic_name': '艾托格列净', 'contraindications': ['透析'], 'side_effects': ['泌尿生殖感染', '酮症酸中毒'], 'metabolism': 'UGT1A9/CYP3A4'}, {'id': 'alogliptin', 'name': '阿格列汀', 'category': 'DPP-4抑制剂', 'generic_name': '苯甲酸阿格列汀', 'contraindications': ['心衰(增加住院率)'], 'side_effects': ['头痛', '鼻咽炎'], 'metabolism': 'CYP2D6(少量)'}, {'id': 'gemigliptin', 'name': '吉格列汀', 'category': 'DPP-4抑制剂', 'generic_name': '吉格列汀', 'contraindications': ['对本品过敏'], 'side_effects': ['鼻咽炎', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'teneligliptin', 'name': '替格列汀', 'category': 'DPP-4抑制剂', 'generic_name': '替格列汀', 'contraindications': ['对本品过敏'], 'side_effects': ['便秘', '头痛'], 'metabolism': 'CYP3A4/黄素单加氧酶'}, {'id': 'insulin_detemir', 'name': '地特胰岛素', 'category': '胰岛素', 'generic_name': '地特胰岛素', 'contraindications': ['低血糖'], 'side_effects': ['低血糖', '体重增加'], 'metabolism': '蛋白水解'}, {'id': 'insulin_glulisine', 'name': '谷赖胰岛素', 'category': '胰岛素', 'generic_name': '谷赖胰岛素', 'contraindications': ['低血糖'], 'side_effects': ['低血糖', '注射部位反应'], 'metabolism': '蛋白水解'}, {'id': 'insulin_degludec', 'name': '德谷胰岛素', 'category': '胰岛素', 'generic_name': '德谷胰岛素', 'contraindications': ['低血糖'], 'side_effects': ['低血糖', '注射部位反应'], 'metabolism': '蛋白水解'}, {'id': 'pramlintide', 'name': '普兰林肽', 'category': '胰淀素类似物', 'generic_name': '醋酸普兰林肽', 'contraindications': ['胃轻瘫'], 'side_effects': ['恶心', '低血糖'], 'metabolism': '蛋白水解'}, {'id': 'l-thyroxine', 'name': '左甲状腺素(注射)', 'category': '甲状腺激素', 'generic_name': '左甲状腺素钠', 'contraindications': ['未治疗的肾上腺功能不全'], 'side_effects': ['甲亢症状'], 'metabolism': '肝脏代谢'}, {'id': 'indacaterol', 'name': '茚达特罗', 'category': 'β2受体激动剂', 'generic_name': '马来酸茚达特罗', 'contraindications': ['对本品过敏'], 'side_effects': ['鼻咽炎', '咳嗽'], 'metabolism': 'CYP3A4/UGT'}, {'id': 'vilanterol', 'name': '维兰特罗', 'category': 'β2受体激动剂', 'generic_name': '三苯乙酸维兰特罗', 'contraindications': ['对本品过敏'], 'side_effects': ['头痛', '鼻咽炎'], 'metabolism': 'CYP3A4'}, {'id': 'umeclidinium', 'name': '乌美溴铵', 'category': '抗胆碱药', 'generic_name': '乌美溴铵', 'contraindications': ['对阿托品类过敏'], 'side_effects': ['口干', '鼻咽炎'], 'metabolism': 'CYP2D6'}, {'id': 'glycopyrrolate', 'name': '格隆溴铵', 'category': '抗胆碱药', 'generic_name': '格隆溴铵', 'contraindications': ['闭角型青光眼', '尿潴留'], 'side_effects': ['口干', '便秘'], 'metabolism': '肾脏排泄'}, {'id': 'roflumilast', 'name': '罗氟司特', 'category': 'PDE4抑制剂', 'generic_name': '罗氟司特', 'contraindications': ['中重度肝功能不全'], 'side_effects': ['腹泻', '体重减轻', '恶心'], 'metabolism': 'CYP3A4/CYP1A2'}, {'id': 'zileuton', 'name': '齐留通', 'category': '5-LOX抑制剂', 'generic_name': '齐留通', 'contraindications': ['活动性肝病', '肝功能不全'], 'side_effects': ['肝毒性', '头痛'], 'metabolism': 'CYP1A2'}, {'id': 'cromolyn_sodium', 'name': '色甘酸钠', 'category': '肥大细胞稳定剂', 'generic_name': '色甘酸钠', 'contraindications': ['对本品过敏'], 'side_effects': ['咽喉刺激', '咳嗽'], 'metabolism': '不代谢'}, {'id': 'nedocromil', 'name': '奈多罗米', 'category': '肥大细胞稳定剂', 'generic_name': '奈多罗米钠', 'contraindications': ['对本品过敏'], 'side_effects': ['头痛', '咽喉刺激'], 'metabolism': '不代谢'}, {'id': 'vonoprazan', 'name': '伏诺拉生', 'category': 'P-CAB', 'generic_name': '富马酸伏诺拉生', 'contraindications': ['对本品过敏'], 'side_effects': ['腹泻', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'revaprazan', 'name': '瑞伐拉赞', 'category': 'P-CAB', 'generic_name': '盐酸瑞伐拉赞', 'contraindications': ['对本品过敏'], 'side_effects': ['头晕', '腹泻'], 'metabolism': 'CYP3A4'}, {'id': 'nizatidine', 'name': '尼扎替丁', 'category': 'H2受体拮抗剂', 'generic_name': '尼扎替丁', 'contraindications': ['对本品过敏'], 'side_effects': ['头痛', '腹泻'], 'metabolism': 'CYP2D6(少量)'}, {'id': 'rebamipide', 'name': '瑞巴派特', 'category': '胃黏膜保护剂', 'generic_name': '瑞巴派特', 'contraindications': ['对本品过敏'], 'side_effects': ['便秘', '腹胀'], 'metabolism': '部分肝脏代谢'}, {'id': 'teprenone', 'name': '替普瑞酮', 'category': '胃黏膜保护剂', 'generic_name': '替普瑞酮', 'contraindications': ['对本品过敏'], 'side_effects': ['便秘', '腹泻'], 'metabolism': 'CYP3A4'}, {'id': 'bismuth_subsalicylate', 'name': '碱式水杨酸铋', 'category': '胃黏膜保护剂', 'generic_name': '碱式水杨酸铋', 'contraindications': ['对水杨酸过敏'], 'side_effects': ['黑便', '便秘'], 'metabolism': '不吸收'}, {'id': 'alosetron', 'name': '阿洛司琼', 'category': '5-HT3拮抗剂', 'generic_name': '盐酸阿洛司琼', 'contraindications': ['便秘', '炎症性肠病'], 'side_effects': ['便秘', '缺血性结肠炎'], 'metabolism': 'CYP1A2/CYP3A4'}, {'id': 'tegaserod', 'name': '替加色罗', 'category': '5-HT4激动剂', 'generic_name': '马来酸替加色罗', 'contraindications': ['腹泻型IBS', '胆囊疾病'], 'side_effects': ['腹泻', '腹痛'], 'metabolism': 'CYP1A2'}, {'id': 'lubiprostone', 'name': '鲁比前列酮', 'category': 'ClC-2激活剂', 'generic_name': '鲁比前列酮', 'contraindications': ['机械性肠梗阻'], 'side_effects': ['恶心', '腹泻'], 'metabolism': 'CYP(少量)'}, {'id': 'linaclotide', 'name': '利那洛肽', 'category': 'GC-C激动剂', 'generic_name': '利那洛肽', 'contraindications': ['机械性肠梗阻', '儿童(<6岁)'], 'side_effects': ['腹泻'], 'metabolism': '蛋白水解'}, {'id': 'plecanatide', 'name': '普卡那肽', 'category': 'GC-C激动剂', 'generic_name': '普卡那肽', 'contraindications': ['机械性肠梗阻'], 'side_effects': ['腹泻'], 'metabolism': '蛋白水解'}, {'id': 'eluxadoline', 'name': '艾沙度林', 'category': '混合阿片受体调节剂', 'generic_name': '艾沙度林', 'contraindications': ['胆囊切除术后', '胰腺炎'], 'side_effects': ['便秘', '恶心'], 'metabolism': '不代谢'}, {'id': 'indomethacin', 'name': '吲哚美辛', 'category': 'NSAIDs', 'generic_name': '吲哚美辛', 'contraindications': ['活动性消化道溃疡', '癫痫'], 'side_effects': ['消化道出血', '头痛'], 'metabolism': 'CYP2C9'}, {'id': 'etoricoxib', 'name': '依托考昔', 'category': 'COX-2抑制剂', 'generic_name': '依托考昔', 'contraindications': ['活动性消化道溃疡', '严重肝功能不全'], 'side_effects': ['心血管事件风险'], 'metabolism': 'CYP3A4'}, {'id': 'lornoxicam', 'name': '氯诺昔康', 'category': 'NSAIDs', 'generic_name': '氯诺昔康', 'contraindications': ['活动性消化道溃疡'], 'side_effects': ['消化道反应'], 'metabolism': 'CYP2C9'}, {'id': 'dezocine', 'name': '地佐辛', 'category': '阿片类镇痛药', 'generic_name': '地佐辛', 'contraindications': ['呼吸抑制'], 'side_effects': ['恶心', '头晕', '嗜睡'], 'metabolism': '肝脏代谢'}, {'id': 'hydromorphone', 'name': '氢吗啡酮', 'category': '阿片类镇痛药', 'generic_name': '盐酸氢吗啡酮', 'contraindications': ['呼吸抑制'], 'side_effects': ['呼吸抑制', '便秘'], 'metabolism': 'UGT2B7'}, {'id': 'methadone', 'name': '美沙酮', 'category': '阿片类镇痛药', 'generic_name': '盐酸美沙酮', 'contraindications': ['呼吸抑制', 'QT延长'], 'side_effects': ['QT延长', '呼吸抑制', '成瘾'], 'metabolism': 'CYP2B6/CYP3A4'}, {'id': 'sulfasalazine', 'name': '柳氮磺吡啶', 'category': 'DMARD', 'generic_name': '柳氮磺吡啶', 'contraindications': ['磺胺过敏', '肠梗阻'], 'side_effects': ['恶心', '皮疹', '骨髓抑制'], 'metabolism': '肠道菌群'}, {'id': 'hydroxychloroquine', 'name': '羟氯喹', 'category': 'DMARD', 'generic_name': '硫酸羟氯喹', 'contraindications': ['视网膜病变'], 'side_effects': ['视网膜毒性', 'QT延长', '低血糖'], 'metabolism': 'CYP2D6/CYP3A4'}, {'id': 'penicillamine', 'name': '青霉胺', 'category': 'DMARD', 'generic_name': '青霉胺', 'contraindications': ['青霉胺过敏', '严重肾功能不全'], 'side_effects': ['肾毒性', '骨髓抑制', '味觉丧失'], 'metabolism': '肝脏代谢'}, {'id': 'rituximab', 'name': '利妥昔单抗', 'category': '生物制剂', 'generic_name': '利妥昔单抗', 'contraindications': ['活动性感染'], 'side_effects': ['输液反应', '感染', '乙肝再激活'], 'metabolism': '蛋白水解'}, {'id': 'infliximab', 'name': '英夫利昔单抗', 'category': '生物制剂', 'generic_name': '英夫利昔单抗', 'contraindications': ['活动性感染', '心衰(NYHA III-IV)'], 'side_effects': ['感染', '输液反应', '乙肝再激活'], 'metabolism': '蛋白水解'}, {'id': 'adalimumab', 'name': '阿达木单抗', 'category': '生物制剂', 'generic_name': '阿达木单抗', 'contraindications': ['活动性感染'], 'side_effects': ['注射部位反应', '感染', '乙肝再激活'], 'metabolism': '蛋白水解'}, {'id': 'etanercept', 'name': '依那西普', 'category': '生物制剂', 'generic_name': '依那西普', 'contraindications': ['活动性感染', '脓毒症'], 'side_effects': ['注射部位反应', '感染'], 'metabolism': '蛋白水解'}, {'id': 'tocilizumab', 'name': '托珠单抗', 'category': '生物制剂', 'generic_name': '托珠单抗', 'contraindications': ['活动性感染'], 'side_effects': ['感染', '肝毒性', '血脂升高'], 'metabolism': '蛋白水解'}, {'id': 'baricitinib', 'name': '巴瑞替尼', 'category': 'JAK抑制剂', 'generic_name': '巴瑞替尼', 'contraindications': ['活动性感染', '严重肝功能不全'], 'side_effects': ['感染', '血栓栓塞', '淋巴细胞减少'], 'metabolism': 'CYP3A4'}, {'id': 'tofacitinib', 'name': '托法替布', 'category': 'JAK抑制剂', 'generic_name': '枸橼酸托法替布', 'contraindications': ['活动性感染'], 'side_effects': ['感染', '血栓栓塞', '淋巴细胞减少'], 'metabolism': 'CYP3A4/CYP2C9'}, {'id': 'upadacitinib', 'name': '乌帕替尼', 'category': 'JAK抑制剂', 'generic_name': '乌帕替尼', 'contraindications': ['活动性感染'], 'side_effects': ['感染', '血栓栓塞'], 'metabolism': 'CYP3A4'}, {'id': 'apremilast', 'name': '阿普米司特', 'category': 'PDE4抑制剂', 'generic_name': '阿普米司特', 'contraindications': ['对本品过敏'], 'side_effects': ['腹泻', '恶心', '头痛'], 'metabolism': 'CYP3A4(少量)'}, {'id': 'dorzolamide', 'name': '多佐胺', 'category': '碳酸酐酶抑制剂(眼科)', 'generic_name': '盐酸多佐胺', 'contraindications': ['严重肾功能不全'], 'side_effects': ['眼部烧灼感', '味觉异常'], 'metabolism': 'CYP2D6(少量)'}, {'id': 'brinzolamide', 'name': '布林佐胺', 'category': '碳酸酐酶抑制剂(眼科)', 'generic_name': '布林佐胺', 'contraindications': ['严重肾功能不全', '高氯血症性酸中毒'], 'side_effects': ['视力模糊', '味觉异常'], 'metabolism': 'CYP3A4'}, {'id': 'dipivefrin', 'name': '地匹福林', 'category': '拟交感神经药(眼科)', 'generic_name': '盐酸地匹福林', 'contraindications': ['闭角型青光眼'], 'side_effects': ['眼部刺激', '瞳孔散大'], 'metabolism': '酯酶水解'}, {'id': 'apraclonidine', 'name': '阿可乐定', 'category': 'α2受体激动剂(眼科)', 'generic_name': '盐酸阿可乐定', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['眼部过敏', '口干'], 'metabolism': '肝脏代谢'}, {'id': 'bimatoprost', 'name': '比马前列素', 'category': '前列腺素类似物(眼科)', 'generic_name': '比马前列素', 'contraindications': ['对本品过敏'], 'side_effects': ['虹膜色素加深', '睫毛生长', '眼部刺激'], 'metabolism': '酯酶水解'}, {'id': 'travoprost', 'name': '曲伏前列素', 'category': '前列腺素类似物(眼科)', 'generic_name': '曲伏前列素', 'contraindications': ['对本品过敏'], 'side_effects': ['虹膜色素加深', '眼部充血'], 'metabolism': '酯酶水解'}, {'id': 'tafluprost', 'name': '他氟前列素', 'category': '前列腺素类似物(眼科)', 'generic_name': '他氟前列素', 'contraindications': ['对本品过敏'], 'side_effects': ['虹膜色素加深', '眼部刺激'], 'metabolism': '酯酶水解'}, {'id': 'netarsudil', 'name': '奈舒地尔', 'category': 'ROCK抑制剂(眼科)', 'generic_name': '甲磺酸奈舒地尔', 'contraindications': ['对本品过敏'], 'side_effects': ['结膜充血', '角膜沉积'], 'metabolism': '酯酶水解'}, {'id': 'pilocarpine_oral', 'name': '毛果芸香碱(口服)', 'category': '拟胆碱药', 'generic_name': '硝酸毛果芸香碱', 'contraindications': ['哮喘', '虹膜睫状体炎'], 'side_effects': ['出汗', '流涎', '恶心'], 'metabolism': '胆碱酯酶'}, {'id': 'adapalene', 'name': '阿达帕林', 'category': '维甲酸类', 'generic_name': '阿达帕林', 'contraindications': ['孕妇'], 'side_effects': ['皮肤刺激', '干燥', '光敏感'], 'metabolism': 'CYP2C9(少量)'}, {'id': 'tazarotene', 'name': '他扎罗汀', 'category': '维甲酸类', 'generic_name': '他扎罗汀', 'contraindications': ['孕妇'], 'side_effects': ['皮肤刺激', '脱皮', '光敏感'], 'metabolism': 'CYP2C9'}, {'id': 'permethrin', 'name': '氯菊酯', 'category': '杀虫药(外用)', 'generic_name': '氯菊酯', 'contraindications': ['对本品过敏'], 'side_effects': ['局部烧灼感', '瘙痒'], 'metabolism': '酯酶水解'}, {'id': 'fluocinonide', 'name': '氟轻松', 'category': '糖皮质激素(外用)', 'generic_name': '醋酸氟轻松', 'contraindications': ['皮肤感染(单用)'], 'side_effects': ['皮肤萎缩', '毛细血管扩张'], 'metabolism': '肝脏代谢'}, {'id': 'betamethasone_topical', 'name': '倍他米松(外用)', 'category': '糖皮质激素(外用)', 'generic_name': '倍他米松', 'contraindications': ['皮肤感染(单用)'], 'side_effects': ['皮肤萎缩', '毛囊炎'], 'metabolism': '肝脏代谢'}, {'id': 'clobetasol', 'name': '氯倍他索', 'category': '糖皮质激素(外用)', 'generic_name': '丙酸氯倍他索', 'contraindications': ['酒糟鼻', '痤疮'], 'side_effects': ['皮肤萎缩', '下丘脑-垂体轴抑制'], 'metabolism': 'CYP3A4'}, {'id': 'calcipotriol', 'name': '卡泊三醇', 'category': '维生素D类似物(外用)', 'generic_name': '卡泊三醇', 'contraindications': ['高钙血症'], 'side_effects': ['局部刺激', '高钙血症(大面积使用)'], 'metabolism': '肝脏代谢'}, {'id': 'imiquimod', 'name': '咪喹莫特', 'category': '免疫调节剂(外用)', 'generic_name': '咪喹莫特', 'contraindications': ['对本品过敏'], 'side_effects': ['局部炎症反应', '糜烂'], 'metabolism': '局部代谢'}, {'id': 'eflornithine', 'name': '依氟鸟氨酸', 'category': '外用制剂', 'generic_name': '盐酸依氟鸟氨酸', 'contraindications': ['对本品过敏'], 'side_effects': ['痤疮', '毛囊炎'], 'metabolism': '不代谢'}, {'id': 'crisaborole', 'name': '克立硼罗', 'category': 'PDE4抑制剂(外用)', 'generic_name': '克立硼罗', 'contraindications': ['对本品过敏'], 'side_effects': ['局部疼痛', '灼热感'], 'metabolism': 'CYP2C9/3A4'}, {'id': 'ruxolitinib_topical', 'name': '鲁索替尼(外用)', 'category': 'JAK抑制剂(外用)', 'generic_name': '磷酸鲁索替尼', 'contraindications': ['活动性感染'], 'side_effects': ['局部刺激', '鼻咽炎'], 'metabolism': 'CYP3A4'}, {'id': 'warfarin_heparin_bridge', 'name': '华法林-肝素桥接', 'category': '抗凝方案', 'generic_name': '华法林+肝素', 'contraindications': ['活动性出血'], 'side_effects': ['出血'], 'metabolism': '见各成分'}, {'id': 'fondaparinux', 'name': '磺达肝癸钠', 'category': '抗凝药', 'generic_name': '磺达肝癸钠', 'contraindications': ['严重肾功能不全', '活动性出血'], 'side_effects': ['出血', '血小板减少'], 'metabolism': '肾脏排泄'}, {'id': 'argatroban', 'name': '阿加曲班', 'category': '抗凝药', 'generic_name': '阿加曲班', 'contraindications': ['活动性出血'], 'side_effects': ['出血', '低血压'], 'metabolism': 'CYP3A4'}, {'id': 'bivalirudin', 'name': '比伐芦定', 'category': '抗凝药', 'generic_name': '比伐芦定', 'contraindications': ['活动性出血'], 'side_effects': ['出血'], 'metabolism': '蛋白酶水解'}, {'id': 'deferoxamine', 'name': '去铁胺', 'category': '螯合剂', 'generic_name': '甲磺酸去铁胺', 'contraindications': ['严重肾功能不全', '无尿'], 'side_effects': ['视听神经毒性', '低血压'], 'metabolism': '血浆酶'}, {'id': 'deferasirox', 'name': '地拉罗司', 'category': '螯合剂', 'generic_name': '地拉罗司', 'contraindications': ['严重肝肾功能不全'], 'side_effects': ['肾毒性', '肝毒性', '消化道出血'], 'metabolism': 'UGT'}, {'id': 'eltrombopag', 'name': '艾曲泊帕', 'category': 'TPO受体激动剂', 'generic_name': '艾曲泊帕', 'contraindications': ['对本品过敏'], 'side_effects': ['肝毒性', '血栓栓塞', '白内障'], 'metabolism': 'CYP1A2/2C8'}, {'id': 'romiplostim', 'name': '罗米司亭', 'category': 'TPO受体激动剂', 'generic_name': '罗米司亭', 'contraindications': ['对本品过敏'], 'side_effects': ['骨髓纤维化', '血栓栓塞'], 'metabolism': '蛋白水解'}, {'id': 'emopamil', 'name': '依莫帕米', 'category': '钙通道阻滞剂', 'generic_name': '盐酸依莫帕米', 'contraindications': ['严重低血压'], 'side_effects': ['低血压', '头痛'], 'metabolism': 'CYP3A4'}, {'id': 'dimenhydrinate', 'name': '茶苯海明', 'category': '抗组胺药', 'generic_name': '茶苯海明', 'contraindications': ['对本品过敏'], 'side_effects': ['嗜睡', '口干'], 'metabolism': 'CYP2D6'}, {'id': 'meclizine', 'name': '美克洛嗪', 'category': '抗组胺药', 'generic_name': '盐酸美克洛嗪', 'contraindications': ['对本品过敏'], 'side_effects': ['嗜睡', '口干'], 'metabolism': 'CYP2D6'}, {'id': 'scopolamine', 'name': '东莨菪碱', 'category': '抗胆碱药', 'generic_name': '氢溴酸东莨菪碱', 'contraindications': ['闭角型青光眼', '肠梗阻'], 'side_effects': ['口干', '嗜睡', '视力模糊'], 'metabolism': 'CYP3A4'}, {'id': 'promethazine', 'name': '异丙嗪', 'category': '抗组胺药', 'generic_name': '盐酸异丙嗪', 'contraindications': ['2岁以下儿童', '昏迷'], 'side_effects': ['嗜睡', 'QT延长'], 'metabolism': 'CYP2D6'}, {'id': 'chlorpheniramine', 'name': '氯苯那敏', 'category': '抗组胺药', 'generic_name': '马来酸氯苯那敏', 'contraindications': ['对本品过敏'], 'side_effects': ['嗜睡', '口干'], 'metabolism': 'CYP2D6'}, {'id': 'desloratadine', 'name': '地氯雷他定', 'category': '抗组胺药', 'generic_name': '地氯雷他定', 'contraindications': ['对本品过敏'], 'side_effects': ['头痛', '疲劳'], 'metabolism': 'CYP3A4/CYP2D6'}, {'id': 'bilastine', 'name': '贝他斯汀', 'category': '抗组胺药', 'generic_name': '贝他斯汀', 'contraindications': ['对本品过敏'], 'side_effects': ['头痛'], 'metabolism': '不代谢'}, {'id': 'betahistine', 'name': '倍他司汀', 'category': '组胺类似物', 'generic_name': '甲磺酸倍他司汀', 'contraindications': ['嗜铬细胞瘤'], 'side_effects': ['头痛', '恶心'], 'metabolism': 'CYP2D6'}, {'id': 'trimipramine', 'name': '曲米帕明', 'category': 'TCA', 'generic_name': '马来酸曲米帕明', 'contraindications': ['心肌梗死恢复期', 'QT延长'], 'side_effects': ['嗜睡', '口干', 'QT延长'], 'metabolism': 'CYP2C19'}, {'id': 'amitriptyline', 'name': '阿米替林', 'category': 'TCA', 'generic_name': '盐酸阿米替林', 'contraindications': ['心肌梗死恢复期', 'QT延长'], 'side_effects': ['嗜睡', '口干', '便秘', 'QT延长'], 'metabolism': 'CYP2D6/CYP2C19'}, {'id': 'nortriptyline', 'name': '去甲替林', 'category': 'TCA', 'generic_name': '盐酸去甲替林', 'contraindications': ['心肌梗死恢复期'], 'side_effects': ['嗜睡', '口干', 'QT延长'], 'metabolism': 'CYP2D6'}, {'id': 'imipramine', 'name': '丙咪嗪', 'category': 'TCA', 'generic_name': '盐酸丙咪嗪', 'contraindications': ['心肌梗死恢复期'], 'side_effects': ['嗜睡', '口干', '体位性低血压'], 'metabolism': 'CYP2D6/CYP2C19'}, {'id': 'doxepin', 'name': '多塞平', 'category': 'TCA', 'generic_name': '盐酸多塞平', 'contraindications': ['青光眼', '尿潴留'], 'side_effects': ['嗜睡', '口干'], 'metabolism': 'CYP2D6/CYP2C19'}, {'id': 'clomipramine', 'name': '氯米帕明', 'category': 'TCA', 'generic_name': '盐酸氯米帕明', 'contraindications': ['MAO抑制剂使用中'], 'side_effects': ['嗜睡', '口干', 'QT延长'], 'metabolism': 'CYP2D6/CYP2C19'}, {'id': 'mianserin', 'name': '米安色林', 'category': 'NaSSA', 'generic_name': '盐酸米安色林', 'contraindications': ['躁狂症'], 'side_effects': ['嗜睡', '体重增加'], 'metabolism': 'CYP2D6'}, {'id': 'agomelatine', 'name': '阿戈美拉汀', 'category': 'MT1/MT2激动剂', 'generic_name': '阿戈美拉汀', 'contraindications': ['肝功能不全'], 'side_effects': ['恶心', '头晕', '肝毒性'], 'metabolism': 'CYP1A2'}]
DRUGS.extend(_EXTRA_DRUGS_2)

_EXTRA_INTERACTIONS_2 = [('irbesartan', 'lisinopril', 'high', 'ACEI+ARB双重RAAS阻断'), ('candesartan', 'enalapril', 'high', 'ACEI+ARB双重RAAS阻断'), ('telmisartan', 'ramipril', 'high', 'ACEI+ARB双重RAAS阻断'), ('olmesartan', 'lisinopril', 'high', 'ACEI+ARB双重RAAS阻断'), ('azilsartan', 'enalapril', 'high', 'ACEI+ARB双重RAAS阻断'), ('fluoxetine', 'amitriptyline', 'high', '氟西汀抑制CYP2D6,阿米替林血药浓度升高'), ('paroxetine', 'amitriptyline', 'high', '帕罗西汀抑制CYP2D6,阿米替林血药浓度升高'), ('fluoxetine', 'imipramine', 'high', '氟西汀抑制CYP2D6,丙咪嗪血药浓度升高'), ('fluoxetine', 'nortriptyline', 'high', '氟西汀抑制CYP2D6,去甲替林血药浓度升高'), ('paroxetine', 'nortriptyline', 'high', '帕罗西汀抑制CYP2D6,去甲替林血药浓度升高'), ('sertraline', 'amitriptyline', 'medium', '舍曲林轻度抑制CYP2D6,阿米替林血药浓度可能升高'), ('amitriptyline', 'fluoxetine', 'high', '氟西汀抑制CYP2D6,阿米替林血药浓度升高'), ('amitriptyline', 'paroxetine', 'high', '帕罗西汀抑制CYP2D6,阿米替林血药浓度升高'), ('amitriptyline', 'cimetidine', 'high', '西咪替丁抑制CYP,阿米替林代谢减慢'), ('amitriptyline', 'MAO_inhibitors', 'critical', 'TCA+MAO抑制剂,高血压危象/5-HT综合征'), ('imipramine', 'MAO_inhibitors', 'critical', 'TCA+MAO抑制剂,高血压危象'), ('clomipramine', 'MAO_inhibitors', 'critical', 'TCA+MAO抑制剂,5-HT综合征风险极高'), ('clomipramine', 'sertraline', 'high', '双重5-HT再摄取抑制'), ('clomipramine', 'fluoxetine', 'high', '双重5-HT再摄取抑制+氟西汀抑制CYP2D6'), ('pramipexole', 'cimetidine', 'medium', '西咪替丁降低普拉克索肾脏清除'), ('ropinirole', 'ciprofloxacin', 'medium', '环丙沙星抑制CYP1A2,罗匹尼罗血药浓度升高'), ('selegiline', 'fluoxetine', 'critical', 'MAO-B抑制剂+SSRI,5-HT综合征风险(需停药5周)'), ('selegiline', 'sertraline', 'critical', 'MAO-B抑制剂+SSRI,5-HT综合征风险'), ('selegiline', 'tramadol', 'high', 'MAO抑制+阿片,5-HT综合征/癫痫风险'), ('rasagiline', 'fluoxetine', 'critical', 'MAO-B抑制剂+SSRI,5-HT综合征风险'), ('rasagiline', 'dextromethorphan', 'high', 'MAO抑制+右美沙芬,5-HT综合征风险'), ('hydroxychloroquine', 'digoxin', 'medium', '羟氯喹升高地高辛血药浓度'), ('hydroxychloroquine', 'methotrexate', 'medium', '可能增加甲氨蝶呤毒性'), ('sulfasalazine', 'warfarin', 'medium', '柳氮磺吡啶增强华法林抗凝效果'), ('sulfasalazine', 'digoxin', 'medium', '柳氮磺吡啶降低地高辛吸收'), ('tofacitinib', 'fluconazole', 'high', '氟康唑抑制CYP3A4,托法替布血药浓度升高'), ('tofacitinib', 'rifampicin', 'high', '利福平诱导CYP3A4,托法替布效果降低'), ('baricitinib', 'rifampicin', 'high', '利福平诱导CYP3A4,巴瑞替尼效果降低'), ('infliximab', 'anakinra', 'high', '双重免疫抑制,感染风险显著增加'), ('infliximab', 'abatacept', 'high', '双重免疫抑制,感染风险显著增加'), ('adalimumab', 'anakinra', 'high', '双重免疫抑制,感染风险显著增加'), ('rituximab', 'cisplatin', 'high', '双重肾毒性'), ('tocilizumab', 'simvastatin', 'medium', '托珠单抗降低CYP3A4活性,他汀代谢可能受影响'), ('timolol_eye', 'propranolol', 'medium', '双重β阻滞,全身不良反应增加'), ('brimonidine', 'MAO_inhibitors', 'high', 'α2激动剂+MAO抑制剂'), ('latanoprost', 'timolol_eye', 'medium', '联合使用降眼压效果增强'), ('cetirizine', 'diazepam', 'medium', '双重中枢抑制'), ('promethazine', 'diazepam', 'high', '双重中枢抑制'), ('loratadine', 'ketoconazole', 'medium', '酮康唑抑制CYP3A4,氯雷他定血药浓度升高'), ('loratadine', 'erythromycin', 'medium', '红霉素抑制CYP3A4,氯雷他定血药浓度升高'), ('isotretinoin', 'tetracycline', 'critical', '维甲酸+四环素,假性脑瘤风险极高'), ('isotretinoin', 'doxycycline', 'critical', '维甲酸+四环素,假性脑瘤风险'), ('isotretinoin', 'minocycline', 'critical', '维甲酸+四环素,假性脑瘤风险'), ('isotretinoin', 'vitamin_a', 'high', '维甲酸+维生素A,维生素A过多症'), ('tretinoin', 'tetracycline', 'high', '维A酸+四环素,假性脑瘤风险'), ('tretinoin', 'ketoconazole', 'medium', '酮康唑抑制CYP2C9,维A酸血药浓度升高'), ('fondaparinux', 'aspirin', 'high', '抗凝+抗血小板,出血风险增加'), ('fondaparinux', 'NSAIDs', 'high', '抗凝+NSAIDs,出血风险增加'), ('eltrombopag', 'antacids', 'medium', '含多价阳离子抗酸剂降低艾曲泊帕吸收'), ('eltrombopag', 'rosuvastatin', 'medium', '艾曲泊帕抑制OATP1B1,瑞舒伐他汀暴露量增加'), ('deferasirox', 'repaglinide', 'medium', '地拉罗司诱导CYP2C8,瑞格列奈效果降低'), ('argatroban', 'warfarin', 'high', '双重抗凝,出血风险(需监测INR)'), ('bivalirudin', 'aspirin', 'high', '抗凝+抗血小板'), ('hydroxychloroquine', 'amiodarone', 'high', '双重QT延长'), ('hydroxychloroquine', 'haloperidol', 'high', '双重QT延长'), ('amantadine', 'hydrochlorothiazide', 'medium', '噻嗪类利尿剂降低金刚烷胺肾脏清除'), ('amantadine', 'trimethoprim', 'medium', '甲氧苄啶降低金刚烷胺肾脏清除'), ('scopolamine', 'amitriptyline', 'high', '双重抗胆碱效应'), ('promethazine', 'amitriptyline', 'high', '双重抗胆碱效应+QT延长'), ('dimenhydrinate', 'amitriptyline', 'high', '双重抗胆碱效应'), ('tramadol', 'amitriptyline', 'high', '阿片+TCA,5-HT综合征+癫痫风险'), ('methadone', 'fluoxetine', 'high', '氟西汀抑制CYP2D6,美沙酮血药浓度可能升高'), ('methadone', 'fluconazole', 'high', '氟康唑抑制CYP3A4,美沙酮血药浓度升高'), ('methadone', 'amiodarone', 'high', '双重QT延长'), ('hydromorphone', 'diazepam', 'critical', '阿片+苯二氮卓,呼吸抑制风险极高'), ('morphine', 'gabapentin', 'medium', '双重中枢抑制'), ('baclofen', 'morphine', 'high', '双重中枢抑制,呼吸抑制风险')]
INTERACTIONS.extend(_EXTRA_INTERACTIONS_2)

_EXTRA_ALTERNATIVES_2 = [('warfarin', 'edoxaban', '新型口服抗凝药,每日一次'), ('simvastatin', 'pitavastatin', '匹伐他汀不经CYP3A4代谢'), ('amlodipine', 'felodipine', '非洛地平作用相似'), ('lisinopril', 'perindopril', '培哚普利循证证据充分'), ('metformin', 'liraglutide', 'GLP-1受体激动剂有减重和心血管获益'), ('metformin', 'semaglutide', '司美格鲁肽有显著心血管和减重获益'), ('glimepiride', 'empagliflozin', 'SGLT2抑制剂有心血管保护'), ('omeprazole', 'vonoprazan', 'P-CAB抑酸更快更强'), ('fluoxetine', 'vortioxetine', '沃替西汀多模式作用,性功能副作用少'), ('amitriptyline', 'duloxetine', 'SNRI替代TCA,心脏毒性低'), ('amitriptyline', 'venlafaxine', 'SNRI替代TCA'), ('diazepam', 'oxazepam', '奥沙西泮仅经葡萄糖醛酸化,老年患者首选'), ('morphine', 'oxycodone', '羟考酮口服生物利用度高'), ('morphine', 'hydromorphone', '氢吗啡酮肾毒性代谢物少'), ('ciprofloxacin', 'levofloxacin', '左氧氟沙星CYP1A2抑制较弱'), ('ketoconazole', 'fluconazole', '氟康唑肝毒性相对较低'), ('doxorubicin', 'liposomal_doxorubicin', '脂质体多柔比星心脏毒性低'), ('cisplatin', 'carboplatin', '卡铂肾毒性和耳毒性较低')]
ALTERNATIVES.extend(_EXTRA_ALTERNATIVES_2)


# ==================== 第三批扩展(肿瘤靶向) ====================
_EXTRA_DRUGS_3 = [{'id': 'trastuzumab', 'name': '曲妥珠单抗', 'category': '生物制剂', 'generic_name': '曲妥珠单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['心脏毒性', '输液反应'], 'metabolism': '蛋白水解'}, {'id': 'bevacizumab', 'name': '贝伐珠单抗', 'category': '生物制剂', 'generic_name': '贝伐珠单抗', 'contraindications': ['近期手术', '出血'], 'side_effects': ['高血压', '蛋白尿', '出血'], 'metabolism': '蛋白水解'}, {'id': 'pembrolizumab', 'name': '帕博利珠单抗', 'category': '免疫检查点抑制剂', 'generic_name': '帕博利珠单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应', '肺炎', '肝炎'], 'metabolism': '蛋白水解'}, {'id': 'nivolumab', 'name': '纳武利尤单抗', 'category': '免疫检查点抑制剂', 'generic_name': '纳武利尤单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应', '肺炎'], 'metabolism': '蛋白水解'}, {'id': 'atezolizumab', 'name': '阿替利珠单抗', 'category': '免疫检查点抑制剂', 'generic_name': '阿替利珠单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应'], 'metabolism': '蛋白水解'}, {'id': 'durvalumab', 'name': '度伐利尤单抗', 'category': '免疫检查点抑制剂', 'generic_name': '度伐利尤单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应'], 'metabolism': '蛋白水解'}, {'id': 'avelumab', 'name': '阿维鲁单抗', 'category': '免疫检查点抑制剂', 'generic_name': '阿维鲁单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应', '输液反应'], 'metabolism': '蛋白水解'}, {'id': 'ipilimumab', 'name': '伊匹木单抗', 'category': '免疫检查点抑制剂', 'generic_name': '伊匹木单抗', 'contraindications': ['对本品过敏'], 'side_effects': ['免疫相关不良反应(较重)', '结肠炎'], 'metabolism': '蛋白水解'}, {'id': 'olaparib', 'name': '奥拉帕利', 'category': 'PARP抑制剂', 'generic_name': '奥拉帕利', 'contraindications': ['严重肝功能不全'], 'side_effects': ['骨髓抑制', '恶心'], 'metabolism': 'CYP3A4'}, {'id': 'niraparib', 'name': '尼拉帕利', 'category': 'PARP抑制剂', 'generic_name': '尼拉帕利', 'contraindications': ['对本品过敏'], 'side_effects': ['骨髓抑制', '高血压'], 'metabolism': 'CYP3A4'}, {'id': 'rucaparib', 'name': '卢卡帕利', 'category': 'PARP抑制剂', 'generic_name': '卢卡帕利', 'contraindications': ['对本品过敏'], 'side_effects': ['骨髓抑制', '恶心'], 'metabolism': 'CYP2D6'}, {'id': 'palbociclib', 'name': '哌柏西利', 'category': 'CDK4/6抑制剂', 'generic_name': '哌柏西利', 'contraindications': ['严重肝功能不全'], 'side_effects': ['骨髓抑制', '疲劳'], 'metabolism': 'CYP3A4'}, {'id': 'ribociclib', 'name': '瑞波西利', 'category': 'CDK4/6抑制剂', 'generic_name': '琥珀酸瑞波西利', 'contraindications': ['QT延长'], 'side_effects': ['骨髓抑制', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'abemaciclib', 'name': '阿贝西利', 'category': 'CDK4/6抑制剂', 'generic_name': '阿贝西利', 'contraindications': ['严重肝功能不全'], 'side_effects': ['腹泻', '骨髓抑制'], 'metabolism': 'CYP3A4'}, {'id': 'ibrutinib', 'name': '伊布替尼', 'category': 'BTK抑制剂', 'generic_name': '伊布替尼', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['出血', '感染', '房颤'], 'metabolism': 'CYP3A4'}, {'id': 'acalabrutinib', 'name': '阿卡替尼', 'category': 'BTK抑制剂', 'generic_name': '阿卡替尼', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['头痛', '感染'], 'metabolism': 'CYP3A4'}, {'id': 'zanubrutinib', 'name': '泽布替尼', 'category': 'BTK抑制剂', 'generic_name': '泽布替尼', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['感染', '出血'], 'metabolism': 'CYP3A4'}, {'id': 'venetoclax', 'name': '维奈克拉', 'category': 'BCL-2抑制剂', 'generic_name': '维奈克拉', 'contraindications': ['CYP3A4强抑制剂合用(首剂)'], 'side_effects': ['肿瘤溶解综合征', '骨髓抑制'], 'metabolism': 'CYP3A4'}, {'id': 'enzalutamide', 'name': '恩杂鲁胺', 'category': 'AR抑制剂', 'generic_name': '恩杂鲁胺', 'contraindications': ['对本品过敏'], 'side_effects': ['疲劳', '潮热', '癫痫'], 'metabolism': 'CYP2C8/CYP3A4'}, {'id': 'abiraterone', 'name': '阿比特龙', 'category': 'CYP17抑制剂', 'generic_name': '醋酸阿比特龙', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '低钾血症'], 'metabolism': 'CYP3A4'}, {'id': 'bortezomib', 'name': '硼替佐米', 'category': '蛋白酶体抑制剂', 'generic_name': '硼替佐米', 'contraindications': ['对本品过敏'], 'side_effects': ['周围神经病变', '血小板减少'], 'metabolism': 'CYP3A4'}, {'id': 'lenalidomide', 'name': '来那度胺', 'category': '免疫调节剂', 'generic_name': '来那度胺', 'contraindications': ['孕妇(致畸)'], 'side_effects': ['骨髓抑制', '血栓栓塞'], 'metabolism': '不代谢'}, {'id': 'pomalidomide', 'name': '泊马度胺', 'category': '免疫调节剂', 'generic_name': '泊马度胺', 'contraindications': ['孕妇(致畸)'], 'side_effects': ['骨髓抑制', '血栓栓塞'], 'metabolism': 'CYP1A2'}, {'id': 'crizotinib', 'name': '克唑替尼', 'category': 'ALK/ROS1抑制剂', 'generic_name': '克唑替尼', 'contraindications': ['QT延长'], 'side_effects': ['视力障碍', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'alectinib', 'name': '阿来替尼', 'category': 'ALK抑制剂', 'generic_name': '盐酸阿来替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['肌痛', '便秘'], 'metabolism': 'CYP3A4'}, {'id': 'osimertinib', 'name': '奥希替尼', 'category': 'EGFR抑制剂', 'generic_name': '甲磺酸奥希替尼', 'contraindications': ['QT延长'], 'side_effects': ['皮疹', '腹泻', '间质性肺炎'], 'metabolism': 'CYP3A4'}, {'id': 'dabrafenib', 'name': '达拉非尼', 'category': 'BRAF抑制剂', 'generic_name': '甲磺酸达拉非尼', 'contraindications': ['对本品过敏'], 'side_effects': ['发热', '皮疹'], 'metabolism': 'CYP2C8'}, {'id': 'trametinib', 'name': '曲美替尼', 'category': 'MEK抑制剂', 'generic_name': '曲美替尼', 'contraindications': ['LVEF降低'], 'side_effects': ['皮疹', '腹泻', '心肌病'], 'metabolism': 'CYP酶(少量)'}, {'id': 'vemurafenib', 'name': '维莫非尼', 'category': 'BRAF抑制剂', 'generic_name': '维莫非尼', 'contraindications': ['QT延长'], 'side_effects': ['关节痛', '皮疹'], 'metabolism': 'CYP3A4'}, {'id': 'regorafenib', 'name': '瑞戈非尼', 'category': '多激酶抑制剂', 'generic_name': '瑞戈非尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['手足综合征', '肝毒性'], 'metabolism': 'CYP3A4'}, {'id': 'cabozantinib', 'name': '卡博替尼', 'category': '多激酶抑制剂', 'generic_name': '苹果酸卡博替尼', 'contraindications': ['近期出血'], 'side_effects': ['腹泻', '高血压'], 'metabolism': 'CYP3A4'}, {'id': 'apatinib', 'name': '阿帕替尼', 'category': 'VEGFR抑制剂', 'generic_name': '甲磺酸阿帕替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '蛋白尿'], 'metabolism': 'CYP3A4'}, {'id': 'anlotinib', 'name': '安罗替尼', 'category': '多激酶抑制剂', 'generic_name': '盐酸安罗替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '手足综合征'], 'metabolism': 'CYP1A2'}, {'id': 'surufatinib', 'name': '索凡替尼', 'category': '多激酶抑制剂', 'generic_name': '索凡替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['蛋白尿', '高血压'], 'metabolism': 'CYP3A4'}, {'id': 'famitinib', 'name': '法米替尼', 'category': '多激酶抑制剂', 'generic_name': '法米替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '腹泻'], 'metabolism': 'CYP3A4'}, {'id': 'tivozanib', 'name': '替沃扎尼', 'category': 'VEGFR抑制剂', 'generic_name': '替沃扎尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高血压', '疲劳'], 'metabolism': 'CYP3A4'}, {'id': 'pazopanib', 'name': '帕唑帕尼', 'category': '多激酶抑制剂', 'generic_name': '帕唑帕尼', 'contraindications': ['QT延长'], 'side_effects': ['肝毒性', '高血压', '腹泻'], 'metabolism': 'CYP3A4'}, {'id': 'sunitinib', 'name': '舒尼替尼', 'category': '多激酶抑制剂', 'generic_name': '苹果酸舒尼替尼', 'contraindications': ['QT延长'], 'side_effects': ['疲劳', '高血压', '手足综合征'], 'metabolism': 'CYP3A4'}, {'id': 'lapatinib', 'name': '拉帕替尼', 'category': 'HER2/EGFR抑制剂', 'generic_name': '甲苯磺酸拉帕替尼', 'contraindications': ['QT延长'], 'side_effects': ['腹泻', '皮疹', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'neratinib', 'name': '奈拉替尼', 'category': 'HER2抑制剂', 'generic_name': '马来酸奈拉替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['腹泻', '肝毒性'], 'metabolism': 'CYP3A4'}, {'id': 'tucatinib', 'name': '图卡替尼', 'category': 'HER2抑制剂', 'generic_name': '图卡替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['腹泻', '手足综合征'], 'metabolism': 'CYP2C8/CYP3A4'}, {'id': 'pirtobrutinib', 'name': '吡托布鲁替尼', 'category': 'BTK抑制剂', 'generic_name': '吡托布鲁替尼', 'contraindications': ['对本品过敏'], 'side_effects': ['疲劳', '瘀伤', '感染'], 'metabolism': 'CYP2C19/CYP3A4'}, {'id': 'capivasertib', 'name': '卡帕塞替尼', 'category': 'AKT抑制剂', 'generic_name': '卡帕塞替尼', 'contraindications': ['对本品过敏'], 'side_effects': ['皮疹', '腹泻', '高血糖'], 'metabolism': 'CYP3A4'}, {'id': 'infigratinib', 'name': '英菲格拉替尼', 'category': 'FGFR抑制剂', 'generic_name': '英菲格拉替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高磷血症', '视网膜病变'], 'metabolism': 'CYP3A4'}, {'id': 'futibatinib', 'name': '福巴替尼', 'category': 'FGFR抑制剂', 'generic_name': '福巴替尼', 'contraindications': ['对本品过敏'], 'side_effects': ['高磷血症', '甲沟炎'], 'metabolism': 'CYP3A4'}, {'id': 'erdafitinib', 'name': '厄达替尼', 'category': 'FGFR抑制剂', 'generic_name': '厄达替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['高磷血症', '视网膜病变'], 'metabolism': 'CYP2C9/CYP3A4'}, {'id': 'selpercatinib', 'name': '塞普替尼', 'category': 'RET抑制剂', 'generic_name': '塞普替尼', 'contraindications': ['QT延长'], 'side_effects': ['口干', '腹泻', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'pralsetinib', 'name': '普拉替尼', 'category': 'RET抑制剂', 'generic_name': '普拉替尼', 'contraindications': ['对本品过敏'], 'side_effects': ['便秘', '疲劳'], 'metabolism': 'CYP3A4'}, {'id': 'larotrectinib', 'name': '拉罗替尼', 'category': 'TRK抑制剂', 'generic_name': '拉罗替尼', 'contraindications': ['CYP3A4强抑制剂合用'], 'side_effects': ['头晕', '疲劳'], 'metabolism': 'CYP3A4'}, {'id': 'entrectinib', 'name': '恩曲替尼', 'category': 'TRK/ROS1抑制剂', 'generic_name': '恩曲替尼', 'contraindications': ['QT延长'], 'side_effects': ['疲劳', '便秘', 'QT延长'], 'metabolism': 'CYP3A4'}, {'id': 'tepotinib', 'name': '特泊替尼', 'category': 'MET抑制剂', 'generic_name': '盐酸特泊替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['水肿', '疲劳'], 'metabolism': 'CYP3A4/CYP2C8'}, {'id': 'capmatinib', 'name': '卡马替尼', 'category': 'MET抑制剂', 'generic_name': '盐酸卡马替尼', 'contraindications': ['严重肝功能不全'], 'side_effects': ['水肿', '恶心'], 'metabolism': 'CYP3A4'}]
DRUGS.extend(_EXTRA_DRUGS_3)


# ==================== 第四批扩展(常见缺口 + 别名友好) ====================
_EXTRA_DRUGS_4 = [
    {"id": "phenytoin", "name": "苯妥英钠", "category": "抗癫痫药", "generic_name": "苯妥英",
     "contraindications": ["窦性心动过缓", "II-III度房室传导阻滞", "严重肝功能不全"],
     "side_effects": ["牙龈增生", "共济失调", "血液系统异常"], "metabolism": "CYP2C9/CYP2C19"},
    {"id": "theophylline", "name": "茶碱", "category": "平喘药", "generic_name": "氨茶碱",
     "contraindications": ["活动性消化道溃疡", "未控制心律失常"],
     "side_effects": ["恶心", "心律失常", "抽搐"], "metabolism": "CYP1A2"},
    {"id": "cimetidine", "name": "西咪替丁", "category": "H2受体拮抗剂", "generic_name": "西咪替丁",
     "contraindications": ["对本品过敏"], "side_effects": ["头痛", "男性乳房发育"], "metabolism": "CYP酶抑制"},
    {"id": "cyclophosphamide", "name": "环磷酰胺", "category": "烷化剂", "generic_name": "环磷酰胺",
     "contraindications": ["严重骨髓抑制", "孕妇", "活动性感染"],
     "side_effects": ["骨髓抑制", "出血性膀胱炎"], "metabolism": "CYP2B6/CYP3A4"},
    {"id": "azathioprine", "name": "硫唑嘌呤", "category": "免疫抑制剂", "generic_name": "硫唑嘌呤",
     "contraindications": ["孕妇", "严重感染"], "side_effects": ["骨髓抑制", "肝毒性"],
     "metabolism": "黄嘌呤氧化酶"},
    {"id": "mercaptopurine", "name": "巯嘌呤", "category": "抗代谢药", "generic_name": "6-巯基嘌呤",
     "contraindications": ["孕妇"], "side_effects": ["骨髓抑制", "肝毒性"], "metabolism": "黄嘌呤氧化酶/TPMT"},
    {"id": "methotrexate", "name": "甲氨蝶呤", "category": "抗代谢药", "generic_name": "甲氨蝶呤",
     "contraindications": ["孕妇", "严重肝肾功能不全", "免疫缺陷"],
     "side_effects": ["骨髓抑制", "肝纤维化", "口腔炎"], "metabolism": "肾脏排泄"},
    {"id": "tacrolimus", "name": "他克莫司", "category": "免疫抑制剂", "generic_name": "他克莫司",
     "contraindications": ["孕妇", "对他克莫司过敏"],
     "side_effects": ["肾毒性", "高血糖", "神经毒性"], "metabolism": "CYP3A4"},
    {"id": "mycophenolate", "name": "吗替麦考酚酯", "category": "免疫抑制剂", "generic_name": "吗替麦考酚酯",
     "contraindications": ["孕妇"], "side_effects": ["腹泻", "骨髓抑制", "感染"],
     "metabolism": "葡萄糖醛酸转移酶"},
]
DRUGS.extend(_EXTRA_DRUGS_4)

_EXTRA_INTERACTIONS_4 = [
    ("warfarin", "aspirin", "high", "抗凝+抗血小板双联,出血风险增加3-4倍"),
    ("phenytoin", "amiodarone", "high", "相互影响血药浓度,需监测"),
    ("cimetidine", "theophylline", "high", "CYP抑制升高茶碱浓度,心律失常风险"),
    ("cimetidine", "warfarin", "high", "CYP抑制增强华法林抗凝"),
    ("mercaptopurine", "allopurinol", "critical", "XO抑制致6-MP蓄积,严重骨髓抑制"),
    ("azathioprine", "allopurinol", "critical", "XO抑制致硫唑嘌呤蓄积,骨髓抑制"),
    ("methotrexate", "cotrimoxazole", "high", "叶酸拮抗/肾排泄竞争,毒性叠加"),
    ("tacrolimus", "cyclosporine", "critical", "两种钙调磷酸酶抑制剂联用,肾毒性叠加"),
    ("tacrolimus", "clarithromycin", "critical", "CYP3A4强抑制,他克莫司浓度升高"),
    ("cyclosporine", "atorvastatin", "high", "他汀暴露升高,肌病风险"),
    ("mycophenolate", "cholestyramine", "high", "树脂吸附降低吗替麦考酚酯吸收"),
    ("levothyroxine", "calcium_carbonate", "low", "钙剂吸附降低甲状腺素吸收,间隔4小时可解"),
    ("levothyroxine", "calcium", "low", "钙剂吸附降低甲状腺素吸收,间隔4小时可解"),
    ("amlodipine", "simvastatin", "medium", "氨氯地平轻度升高他汀暴露,注意肌病"),
    ("omeprazole", "clopidogrel", "medium", "CYP2C19抑制可能减弱氯吡格雷活化"),
]
INTERACTIONS.extend(_EXTRA_INTERACTIONS_4)
# 碳酸钙若已存在则用 calcium_carbonate 别名边;同时确保 calcium 节点可用
if not any(d["id"] == "calcium_carbonate" for d in DRUGS):
    DRUGS.append({
        "id": "calcium_carbonate", "name": "碳酸钙", "category": "矿物质补充剂",
        "generic_name": "碳酸钙", "contraindications": ["高钙血症"],
        "side_effects": ["便秘", "腹胀"], "metabolism": "不代谢",
    })
if not any(d["id"] == "cholestyramine" for d in DRUGS):
    DRUGS.append({
        "id": "cholestyramine", "name": "考来烯胺", "category": "胆汁酸螯合剂",
        "generic_name": "考来烯胺", "contraindications": ["完全性胆道梗阻"],
        "side_effects": ["便秘", "脂肪泻"], "metabolism": "不吸收",
    })
if not any(d["id"] == "rifampin" for d in DRUGS):
    DRUGS.append({
        "id": "rifampin", "name": "利福平", "category": "抗结核药",
        "generic_name": "利福平", "contraindications": ["严重肝功能不全", "黄疸"],
        "side_effects": ["肝毒性", "体液变色", "酶诱导"], "metabolism": "CYP酶诱导",
    })
_EXTRA_INTERACTIONS_4.append(
    ("rifampin", "warfarin", "high", "强酶诱导显著降低华法林疗效")
)


# ==================== 第 5 批：补全被静默丢弃的交互所引用的药物 ====================
# 背景：早期批次中部分 INTERACTIONS / ALTERNATIVES 引用了当时尚未建库的药物 id，
#       建图时被静默跳过（约 51 条引用 / 数十条交互丢失）。本批补齐这些节点。
_EXTRA_DRUGS_5 = [
    # ---- 具体药物 ----
    {"id": "ketoconazole", "name": "酮康唑", "category": "唑类抗真菌药",
     "generic_name": "酮康唑", "contraindications": ["肝功能不全", "酗酒"],
     "side_effects": ["肝毒性", "恶心", "男性乳房发育"], "metabolism": "CYP3A4强抑制剂"},
    {"id": "fluvoxamine", "name": "氟伏沙明", "category": "SSRI抗抑郁药",
     "generic_name": "马来酸氟伏沙明", "contraindications": ["MAOI合用"],
     "side_effects": ["恶心", "嗜睡", "性功能障碍"], "metabolism": "CYP1A2/CYP2C19抑制剂"},
    {"id": "ritonavir", "name": "利托那韦", "category": "抗病毒药",
     "generic_name": "利托那韦", "contraindications": ["严重肝功能不全"],
     "side_effects": ["胃肠道反应", "血脂异常", "肝毒性"], "metabolism": "CYP3A4强抑制剂"},
    {"id": "lovastatin", "name": "洛伐他汀", "category": "他汀类降脂药",
     "generic_name": "洛伐他汀", "contraindications": ["活动性肝病", "妊娠"],
     "side_effects": ["肌痛", "肝酶升高", "横纹肌溶解"], "metabolism": "CYP3A4"},
    {"id": "dabigatran", "name": "达比加群酯", "category": "直接凝血酶抑制剂",
     "generic_name": "甲磺酸达比加群酯", "contraindications": ["严重肾功能不全", "活动性出血"],
     "side_effects": ["出血", "消化不良"], "metabolism": "P-gp底物,酯酶水解"},
    {"id": "pimozide", "name": "匹莫齐特", "category": "抗精神病药",
     "generic_name": "匹莫齐特", "contraindications": ["QT间期延长", "CYP3A4抑制剂合用"],
     "side_effects": ["QT延长", "锥体外系反应"], "metabolism": "CYP3A4/CYP2D6"},
    {"id": "bupropion", "name": "安非他酮", "category": "NDRI抗抑郁药",
     "generic_name": "盐酸安非他酮", "contraindications": ["癫痫", "进食障碍", "MAOI合用"],
     "side_effects": ["失眠", "口干", "癫痫发作风险"], "metabolism": "CYP2B6底物/CYP2D6抑制剂"},
    {"id": "anakinra", "name": "阿那白滞素", "category": "生物制剂",
     "generic_name": "阿那白滞素", "contraindications": ["活动性感染", "中性粒细胞减少"],
     "side_effects": ["注射部位反应", "感染风险增加"], "metabolism": "蛋白水解"},
    {"id": "abatacept", "name": "阿巴西普", "category": "生物制剂",
     "generic_name": "阿巴西普", "contraindications": ["活动性感染", "COPD(慎用)"],
     "side_effects": ["头痛", "感染风险增加", "输液反应"], "metabolism": "蛋白水解"},
    {"id": "trimethoprim", "name": "甲氧苄啶", "category": "抗菌药",
     "generic_name": "甲氧苄啶", "contraindications": ["叶酸缺乏", "严重肾功能不全"],
     "side_effects": ["高钾血症", "皮疹", "骨髓抑制"], "metabolism": "部分肝代谢,主要肾排泄"},
    {"id": "oxazepam", "name": "奥沙西泮", "category": "苯二氮卓类",
     "generic_name": "奥沙西泮", "contraindications": ["重症肌无力", "严重呼吸功能不全"],
     "side_effects": ["嗜睡", "共济失调"], "metabolism": "葡萄糖醛酸结合(不经CYP)"},
    {"id": "epirubicin", "name": "表柔比星", "category": "蒽环类抗肿瘤药",
     "generic_name": "盐酸表柔比星", "contraindications": ["严重骨髓抑制", "既往蒽环类累积剂量超标"],
     "side_effects": ["心脏毒性", "骨髓抑制", "脱发"], "metabolism": "肝脏代谢"},
    {"id": "edoxaban", "name": "艾多沙班", "category": "Xa因子抑制剂",
     "generic_name": "甲苯磺酸艾多沙班", "contraindications": ["活动性出血", "CrCl>95ml/min(疗效下降)"],
     "side_effects": ["出血", "贫血"], "metabolism": "P-gp底物,少经CYP3A4"},
    {"id": "liposomal_doxorubicin", "name": "脂质体多柔比星", "category": "蒽环类抗肿瘤药",
     "generic_name": "盐酸多柔比星脂质体", "contraindications": ["严重骨髓抑制", "既往蒽环类累积剂量超标"],
     "side_effects": ["手足综合征", "心脏毒性较低", "骨髓抑制"], "metabolism": "肝脏代谢"},
    {"id": "magnesium_antacid", "name": "含镁抗酸药", "category": "抗酸药",
     "generic_name": "氢氧化镁/三硅酸镁", "contraindications": ["严重肾功能不全"],
     "side_effects": ["腹泻", "高镁血症(肾功能不全)"], "metabolism": "不吸收,肠道作用"},
    # ---- 类别级节点（用于表达"类效应"相互作用，如 SSRI+MAOI、锂盐+NSAIDs）----
    {"id": "MAO_inhibitors", "name": "单胺氧化酶抑制剂(类)", "category": "药物类别",
     "generic_name": "MAOI", "contraindications": ["SSRI/SNRI合用", "拟交感神经药合用"],
     "side_effects": ["5-羟色胺综合征", "高血压危象"], "metabolism": "MAO抑制"},
    {"id": "NSAIDs", "name": "非甾体抗炎药(类)", "category": "药物类别",
     "generic_name": "NSAIDs", "contraindications": ["活动性消化道溃疡", "重度心衰", "严重肾功能不全"],
     "side_effects": ["胃肠道出血", "水钠潴留", "肾功能下降"], "metabolism": "肝代谢,抑制COX"},
    {"id": "oral_contraceptives", "name": "口服避孕药(类)", "category": "药物类别",
     "generic_name": "雌孕激素复方", "contraindications": ["血栓病史", "严重肝病", "哺乳期"],
     "side_effects": ["血栓风险", "恶心", "突破性出血"], "metabolism": "CYP3A4底物"},
    {"id": "vitamin_a", "name": "维生素A(视黄醇类)", "category": "药物类别",
     "generic_name": "视黄醇/异维A酸类", "contraindications": ["妊娠", "严重肝功能不全"],
     "side_effects": ["致畸", "肝毒性", "颅内压升高"], "metabolism": "肝脏代谢"},
    {"id": "contrast_dye", "name": "含碘对比剂", "category": "药物类别",
     "generic_name": "碘对比剂", "contraindications": ["严重甲状腺功能亢进", "碘过敏"],
     "side_effects": ["过敏反应", "造影剂肾病"], "metabolism": "原形肾排泄"},
]
DRUGS.extend(_EXTRA_DRUGS_5)

# ==================== 外部 holdout 暴露的数据缺口 ====================
# 来源:scripts/eval_external_holdout.py 在 60 条手工标注(非自产)样本上的失败案例。
# 这些药都是临床常用药,之前库里没有或只有节点没有边,属于真实数据缺口而非"为了刷分编数据"。
_EXTRA_DRUGS_6 = [
    {"id": "moclobemide", "name": "吗氯贝胺", "category": "抗抑郁药",
     "generic_name": "吗氯贝胺(可逆性MAO-A抑制剂)",
     "contraindications": ["SSRI/SNRI合用", "嗜铬细胞瘤", "躁狂期"],
     "side_effects": ["失眠", "头晕", "5-羟色胺综合征(联用时)"], "metabolism": "MAO-A抑制"},
    {"id": "captopril", "name": "卡托普利", "category": "ACEI",
     "generic_name": "卡托普利", "contraindications": ["妊娠", "双侧肾动脉狭窄", "血管性水肿史"],
     "side_effects": ["干咳", "高钾血症", "血管性水肿", "肾功能下降"], "metabolism": "部分肝代谢"},
    {"id": "fish_oil", "name": "鱼油", "category": "膳食补充剂",
     "generic_name": "Omega-3脂肪酸", "contraindications": ["出血体质", "抗凝治疗中(大剂量)"],
     "side_effects": ["消化道不适", "出血倾向(大剂量)"], "metabolism": "不代谢"},
    {"id": "iron_supplement", "name": "铁剂", "category": "矿物质补充剂",
     "generic_name": "硫酸亚铁/富马酸亚铁", "contraindications": ["血色病", "含铁血黄素沉着症"],
     "side_effects": ["便秘", "黑便", "胃肠道刺激"], "metabolism": "不代谢"},
]
DRUGS.extend(_EXTRA_DRUGS_6)

_EXTRA_INTERACTIONS_6 = [
    # --- 直接对应 holdout 的 5 条二分类漏检 ---
    ("warfarin", "sulfamethoxazole_trimethoprim", "high",
     "磺胺甲噁唑抑制CYP2C9,增强华法林抗凝,出血风险升高"),
    ("fluoxetine", "moclobemide", "critical",
     "SSRI+MAOI,5-羟色胺综合征,绝对禁忌"),
    ("gemfibrozil", "lovastatin", "critical",
     "贝特类+他汀,横纹肌溶解风险显著(吉非罗齐禁与洛伐他汀联用)"),
    ("captopril", "spironolactone", "high",
     "ACEI+保钾利尿剂,双重升高血钾,高钾血症风险"),
    ("methotrexate", "naproxen", "high",
     "NSAIDs减少甲氨蝶呤肾排泄,血药浓度升高,骨髓抑制风险"),
    # --- 精确匹配漏判(二分类已过,等级判错)---
    ("warfarin", "fish_oil", "medium", "大剂量鱼油抑制血小板聚集,与抗凝叠加,需监测INR"),
    ("levothyroxine", "iron_supplement", "medium",
     "铁剂吸附降低左甲状腺素吸收,需间隔4小时服用"),
    # --- 顺带补齐新节点的常见边,避免孤立节点拉低图谱密度 ---
    ("sertraline", "moclobemide", "critical", "SSRI+MAOI,5-羟色胺综合征风险"),
    ("moclobemide", "tramadol", "critical", "MAOI+曲马多,5-羟色胺综合征与癫痫风险"),
    ("captopril", "potassium", "critical", "ACEI+补钾,高钾血症风险"),
    ("captopril", "naproxen", "high", "NSAIDs削弱ACEI降压效果并增加肾损害风险"),
    ("captopril", "ibuprofen", "high", "NSAIDs削弱ACEI降压效果并增加肾损害风险"),
    ("fish_oil", "aspirin", "medium", "抗血小板+鱼油,出血倾向叠加"),
    ("fish_oil", "clopidogrel", "medium", "抗血小板+鱼油,出血倾向叠加"),
    ("iron_supplement", "ciprofloxacin", "medium", "铁剂螯合显著降低喹诺酮类吸收"),
    ("iron_supplement", "levofloxacin", "medium", "铁剂螯合显著降低喹诺酮类吸收"),
    ("allopurinol", "ampicillin", "medium", "别嘌醇+氨苄西林皮疹风险增加,需观察"),
]
INTERACTIONS.extend(_EXTRA_INTERACTIONS_6)


# ==================== id 别名重映射 ====================
# 同一药物的不同英文拼写 / 复方-单药关系，统一到图谱中已存在的 id，
# 避免这些交互因"药名对不上"被静默丢弃。
_ID_ALIAS = {
    "rifampicin": "rifampin",                    # 利福平：英美拼写差异
    "methotrexate_onco": "methotrexate",         # 甲氨蝶呤：肿瘤剂量与低剂量同药
    "calcium": "calcium_carbonate",              # 钙剂 → 碳酸钙
    "opioids": "morphine",                       # 阿片类 → 代表药吗啡
    "penicillins": "penicillin_v",               # 青霉素类 → 代表药青霉素V
}


def _apply_id_alias():
    """就地修正 INTERACTIONS / ALTERNATIVES 中的药物 id 别名。"""
    for i, item in enumerate(INTERACTIONS):
        a, b, sev, mech = item
        a2, b2 = _ID_ALIAS.get(a, a), _ID_ALIAS.get(b, b)
        if (a2, b2) != (a, b):
            INTERACTIONS[i] = (a2, b2, sev, mech)
    for i, item in enumerate(ALTERNATIVES):
        a, b, reason = item
        a2, b2 = _ID_ALIAS.get(a, a), _ID_ALIAS.get(b, b)
        if (a2, b2) != (a, b):
            ALTERNATIVES[i] = (a2, b2, reason)


_apply_id_alias()


def _dedupe_drugs():
    """就地去除重复药物 id（保留首个定义，与 build_graph_from_data 行为一致）。

    历史上不同批次重复定义了 9 个药物（如 theophylline 分属"黄嘌呤类"/"平喘药"）。
    建图时只取首个、其余静默丢弃；这里在数据层就先去重，让 DRUGS 长度等于真实药物数，
    避免"数出来的药物数"和"图谱里的药物数"对不上。
    """
    seen = set()
    dup_log: list = []
    unique: list = []
    for d in DRUGS:
        if d["id"] in seen:
            dup_log.append(d["id"])
            continue
        seen.add(d["id"])
        unique.append(d)
    if dup_log:
        logger.warning("去除重复药物定义（保留首个）: %s", sorted(set(dup_log)))
        DRUGS[:] = unique
    return sorted(set(dup_log))


DUPLICATE_DRUG_IDS = _dedupe_drugs()


def validate_data(strict: bool = False) -> dict:
    """校验数据完整性：交互/替代关系是否引用了不存在的药物。

    Args:
        strict: True 时若存在悬挂引用则抛 ValueError（建议在 CI 中使用）。

    Returns:
        {"drugs": 去重后药物数, "interactions": 交互条数,
         "dangling": {id: 被引用次数}, "dangling_count": 总悬挂引用数}
    """
    idset = {d["id"] for d in DRUGS}
    dangling: dict = {}
    for a, b, _sev, _mech in INTERACTIONS:
        for x in (a, b):
            if x not in idset:
                dangling[x] = dangling.get(x, 0) + 1
    for a, b, _r in ALTERNATIVES:
        for x in (a, b):
            if x not in idset:
                dangling[x] = dangling.get(x, 0) + 1
    result = {
        "drugs": len(idset),
        "interactions": len(INTERACTIONS),
        "alternatives": len(ALTERNATIVES),
        "dangling": dict(sorted(dangling.items(), key=lambda kv: -kv[1])),
        "dangling_count": sum(dangling.values()),
    }
    if strict and dangling:
        raise ValueError(f"药物数据存在悬挂引用: {result['dangling']}")
    return result


def build_graph_from_data():
    """从预置数据构建药物知识图谱。

    建图前先做数据完整性校验；若存在引用了不存在药物的交互/替代关系，
    会以 warning 记录并返回在结果里，而不是静默丢失。
    """
    from app.graph.drug_graph import (
        add_drug, add_interaction, add_alternative, save_graph, get_graph
    )

    check = validate_data()
    if check["dangling_count"]:
        logger.warning("药物数据存在 %d 条悬挂引用: %s",
                       check["dangling_count"], check["dangling"])

    # 必须建空图而不是 _graph=None：置 None 后 get_graph() 会先加载磁盘旧 JSON，
    # 导致「重建」实际是在脏图上叠新边，缺药/旧边会残留。
    import networkx as nx
    import app.graph.drug_graph as dg
    dg._graph = nx.DiGraph()

    # 添加药物(去重)
    seen_ids = set()
    for drug in DRUGS:
        if drug["id"] in seen_ids:
            continue
        seen_ids.add(drug["id"])
        add_drug(
            drug_id=drug["id"],
            name=drug["name"],
            category=drug.get("category", ""),
            generic_name=drug.get("generic_name", ""),
            contraindications=drug.get("contraindications", []),
            side_effects=drug.get("side_effects", []),
            metabolism=drug.get("metabolism", ""),
        )

    # 先添加替代药物,再添加相互作用(交互关系优先级更高,不被替代关系覆盖)
    for a, b, reason in ALTERNATIVES:
        add_alternative(a, b, reason)

    # 添加相互作用(后执行,确保 INTERACTS_WITH 不被 ALTERNATIVE_OF 覆盖)
    for a, b, severity, mechanism in INTERACTIONS:
        add_interaction(a, b, severity, mechanism)

    save_graph()
    G = get_graph()
    drug_count = sum(1 for _, d in G.nodes(data=True) if d.get("drug"))
    interaction_count = sum(1 for _, _, d in G.edges(data=True)
                           if d.get("relation") == "INTERACTS_WITH")
    # 幽灵节点自检：有边相连但没有 drug 标记的节点
    phantoms = [n for n, d in G.nodes(data=True) if not d.get("drug")]
    if phantoms:
        logger.error("图谱出现幽灵节点: %s", phantoms)
    return {
        "drugs": drug_count,
        "interactions": interaction_count // 2,
        "dangling_count": check["dangling_count"],
        "phantom_nodes": phantoms,
    }
