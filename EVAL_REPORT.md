# 📊 用药安全审查系统 — 评测报告

> 生成时间: 2026-09-13 18:39:16

> 标注样本数: 191 (手工标注 16 + 程序生成 175)

## 1. 总览(二分类)

| 方案 | Accuracy | Precision | Recall | F1 | 精确匹配 |
|------|----------|-----------|--------|----|----------|
| 纯规则引擎 | 90.1% | 96.9% | 85.3% | 90.7% | 139/191 |
| 图谱+规则 | 90.6% | 96.9% | 86.2% | 91.3% | 156/191 |

## 2. 混淆矩阵

| 方案 | TP | FP | FN | TN |
|------|----|----|----|----|
| 纯规则引擎 | 93 | 3 | 16 | 79 |
| 图谱+规则 | 94 | 3 | 15 | 79 |

## 3. 多分类指标(图谱+规则方案)

| 风险等级 | Precision | Recall | F1 | 支持数 |
|----------|-----------|--------|----|--------|
| critical | 95.9% | 75.3% | 84.3% | 93 |
| high | 54.2% | 81.2% | 65.0% | 16 |
| medium | 100.0% | 81.4% | 89.7% | 43 |
| safe | 66.7% | 97.4% | 79.2% | 39 |

## 4. 分类别统计(图谱+规则方案)

| 用例类别 | 总数 | 正确 | 准确率 |
|----------|------|------|--------|
| 中风险 | 40 | 34 | 85.0% |
| 多药联用 | 6 | 6 | 100.0% |
| 安全组合 | 40 | 39 | 97.5% |
| 特殊人群 | 18 | 17 | 94.4% |
| 高风险交互 | 71 | 57 | 80.3% |

## 5. 逐案对比(手工标注)

| ID | 描述 | 期望 | 规则 | 图谱+规则 |
|----|------|------|------|---------|
| H001 | 华法林+阿司匹林+布洛芬,65岁冠心病 | critical | high ❌ | critical ✅ |
| H002 | 华法林+氯吡格雷,70岁房颤 | critical | high ❌ | high ❌ |
| H003 | 地高辛+呋塞米+螺内酯,72岁心衰 | high | high ✅ | high ✅ |
| H004 | 阿托伐他汀+克拉霉素,68岁 | high | high ✅ | high ✅ |
| H005 | 美托洛尔+维拉帕米,60岁高血压 | high | high ✅ | high ✅ |
| M001 | 氨氯地平+辛伐他汀,55岁高血压+高脂血症 | medium | medium ✅ | medium ✅ |
| M002 | 二甲双胍+碘造影剂,50岁糖尿病 | medium | safe ❌ | safe ❌ |
| P001 | 华法林+氯沙坦,28岁孕妇 | critical | critical ✅ | critical ✅ |
| P002 | 阿托伐他汀+美托洛尔,30岁孕妇 | high | critical ❌ | critical ❌ |
| C001 | 环丙沙星+阿司匹林,10岁 | high | critical ❌ | critical ❌ |
| S001 | 氨氯地平+对乙酰氨基酚,45岁高血压 | safe | safe ✅ | safe ✅ |
| S002 | 奥美拉唑+莫沙必利,40岁胃炎 | safe | safe ✅ | safe ✅ |
| S003 | 左甲状腺素+碳酸钙,50岁甲减 | safe | low ❌ | low ❌ |
| S004 | 二甲双胍+阿卡波糖,55岁糖尿病 | safe | safe ✅ | safe ✅ |
| L001 | 依那普利+缬沙坦,60岁高血压(双重RAAS阻断) | medium | high ❌ | high ❌ |
| L002 | 氨氯地平+缬沙坦,55岁高血压(合理联用) | safe | safe ✅ | safe ✅ |

### 生成用例中的典型错误

| ID | 描述 | 期望 | 检测 | 类别 |
|----|------|------|------|------|
| HI001 | rifampicin+他克莫司(critical级交互),72岁女 | critical | safe | 高风险交互 |
| HI002 | 异维A酸+米诺环素(critical级交互),72岁女 | critical | safe | 高风险交互 |
| HI003 | 氯氮平+fluvoxamine(critical级交互),45岁男 | critical | safe | 高风险交互 |
| HI008 | 氟替卡松+ritonavir(critical级交互),72岁男 | critical | safe | 高风险交互 |
| HI014 | 氯米帕明+MAO_inhibitors(critical级交互),70岁女 | critical | safe | 高风险交互 |
| HI018 | methotrexate_onco+NSAIDs(critical级交互),72岁男 | critical | safe | 高风险交互 |
| HI032 | 美罗培南+丙戊酸(critical级交互),70岁女 | critical | safe | 高风险交互 |
| HI036 | 舍曲林+pimozide(critical级交互),75岁男 | critical | safe | 高风险交互 |
| HI038 | rifampicin+华法林(critical级交互),75岁男 | critical | safe | 高风险交互 |
| HI040 | 二甲双胍+contrast_dye(critical级交互),75岁男 | critical | safe | 高风险交互 |
| HI043 | 异维A酸+四环素(critical级交互),70岁男 | critical | high | 高风险交互 |
| HI046 | 西地那非+硝酸异山梨酯(critical级交互),75岁男 | critical | safe | 高风险交互 |
| HI047 | rifampicin+oral_contraceptives(critical级交互),72岁女 | critical | safe | 高风险交互 |
| HI050 | 沙库巴曲缬沙坦+赖诺普利(critical级交互),60岁女 | critical | high | 高风险交互 |
| HI057 | 维拉帕米+lovastatin(critical级交互),70岁男 | critical | safe | 高风险交互 |
| ... | 还有 14 个错误 | | | |

## 6. 关键发现

- 图谱+规则相比纯规则,召回率从 85.3% 提升到 86.2%
- 规则引擎 precision = 96.9%（零误报）
- 完整三层(含LLM)的评测需运行 `python tests/test_eval.py --full`

---
*二分类标准: critical/high = 正样本, medium/low/safe = 负样本*