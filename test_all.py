import time, os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from app.workflow import review_prescription
from app.agents.supervisor_agent import review_multi_agent

cases = [
    ("高危出血", "患者王某,男,65岁,高血压病史10年,2型糖尿病5年\n诊断:冠心病,高血压,2型糖尿病\n处方:\n1. 华法林 2.5mg qd\n2. 阿司匹林 100mg qd\n3. 氨氯地平 5mg qd\n4. 二甲双胍 500mg bid\n5. 布洛芬 400mg prn"),
    ("老年多药", "患者李某,男,72岁,慢性失眠,骨关节炎\n诊断:失眠症,骨关节炎\n处方:\n1. 地西泮 5mg qn\n2. 布洛芬 400mg tid\n3. 阿托伐他汀 20mg qd\n4. 美托洛尔 47.5mg qd"),
    ("孕妇禁忌", "患者张某,女,28岁,孕12周,高血压\n诊断:妊娠期高血压\n处方:\n1. 氯沙坦 50mg qd\n2. 辛伐他汀 20mg qd\n3. 对乙酰氨基酚 500mg prn"),
    ("肝损+他汀", "患者刘某,男,55岁,慢性乙肝,高脂血症\n诊断:慢性乙型肝炎,高脂血症\n处方:\n1. 辛伐他汀 40mg qn\n2. 对乙酰氨基酚 500mg tid\n3. 阿司匹林 100mg qd"),
    ("肾损", "患者陈某,女,70岁,慢性肾病4期,2型糖尿病\n诊断:慢性肾脏病,2型糖尿病\n处方:\n1. 二甲双胍 1000mg bid\n2. 格列本脲 5mg bid\n3. 赖诺普利 20mg qd"),
    ("安全", "患者赵某,女,45岁,高血压\n诊断:高血压\n处方:\n1. 氨氯地平 5mg qd\n2. 对乙酰氨基酚 500mg prn"),
]

for name, text in cases:
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"{'='*50}")
    t0 = time.time()
    try:
        r = review_prescription(text)
        t1 = time.time()
        rx = r.get("prescription")
        drugs = rx.drugs if rx and hasattr(rx, 'drugs') else []
        risk = r.get("risk_assessment")
        ra = risk.overall_risk if risk else "N/A"
        risks = len(risk.risks) if risk else 0
        its = len(r.get("interactions", []))
        rrs = len(r.get("rule_risks", []))
        alts = r.get("alternatives")
        ac = len(alts.suggestions) if alts and hasattr(alts, 'suggestions') else 0
        print(f"  Time: {t1-t0:.0f}s | Drugs: {len(drugs)} | Risk: {ra} | Risks: {risks} | Interactions: {its} | Rules: {rrs} | Alts: {ac}")
    except Exception as e:
        t1 = time.time()
        print(f"  ERROR after {t1-t0:.0f}s: {type(e).__name__}: {e}")

print("\n\nDone.")
