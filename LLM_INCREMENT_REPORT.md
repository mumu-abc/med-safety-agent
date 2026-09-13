# LLM 增量价值评测报告

> 生成时间: 2026-09-13 05:32:38
> 难例数: 9  (parse / reason / negative)

## 1. 为什么需要这份报告

主评测集(77条)中 61 条由图谱程序生成,图谱+规则与「含 LLM」方案 F1 几乎相同,
**无法证明 LLM/Agent 的增量价值**。本报告用「规则/图谱设计时未覆盖」的难例,
拆开测量解析增量与推理增量。

## 2. 三轨对比总览

| 轨道 | 说明 | 精确匹配 | 精确率 | 二分类正确率 |
|------|------|----------|--------|--------------|
| A. Graph+Rules @ 标注药名(无 LLM) | 9 条 | 6/9 | 66.7% | 77.8% |
| C. 解析 + 语义评估 + 规则兜底 | 9 条 | 7/9 | 77.8% | 100.0% |

## 3. 逐案:Oracle 基线 vs Full

| ID | Track | 期望 | A.Oracle | C.Full | A对 | C对 | LLM 增量说明 |
|----|-------|------|----------|--------|-----|-----|--------------|
| LI-P01 | parse | high | high | high | Y | Y | 商品名需 LLM 归一到通用名;图谱按通用名索引,关键词直配会漏 |
| LI-P02 | parse | critical | critical | critical | Y | Y | 口语病历+商品名芬必得;归一后规则命中抗凝+NSAID |
| LI-P03 | parse | high | safe | high | N | Y | 需识别商品名与通用名是同一成分,判定重复用药/剂量加倍 |
| LI-P04 | parse | high | high | high | Y | Y | 强的松不在图谱节点;LLM 应归一为泼尼松,并结合老年+激素+NSAID 判断消化道风险 |
| LI-R01 | reason | high | safe | high | N | Y | 单药、图谱无边、规则不查剂量;需 LLM 判断日剂量上限与肝毒性 |
| LI-R02 | reason | critical | critical | high | Y | N | 肾功能在自由文本中;只有 LLM 解析出 renal_function=impaired,规则引 |
| LI-R03 | reason | critical | critical | critical | Y | Y | 规则可能只覆盖阿片+苯二氮卓;加巴喷丁叠加需综合评估呼吸抑制 |
| LI-N01 | negative | safe | safe | safe | Y | Y | 防止 LLM 因多药/慢病就升级报警 |
| LI-N02 | negative | safe | medium | medium | N | N | 吸收干扰可通过服药时间解决,不应 high |

## 4. LLM 净增量

- Full 修好 Oracle 错判: **2** 条 `['LI-P03', 'LI-R01']`
- Full 弄坏 Oracle 对判: **1** 条 `['LI-R02']`
- 净增量: **+1** 条精确匹配

## 5. 结论(面试可用)

在 9 条「规则/图谱覆盖不到」的难例上:确定性基线精确率 **66.7%**,加入 LLM 解析与语义评估后 **77.8%**,提升 **+11.1%**。

这回答了「为什么不能只写规则引擎」:
1. 自由文本/商品名解析 —— LLM 负责把病历变成结构化药名
2. 剂量、病史、图谱外药理知识 —— LLM 负责语义推理
3. 已知相互作用与硬禁忌 —— 图谱+规则仍是底线,且 overall_risk 不得被 LLM 降级

---
*难例集不替代主评测集;主评测衡量已覆盖分布上的回归,本集衡量分布外增量。*
*Track C 使用单次 structured output 而非 ReAct 工具循环:在部分国产模型上 ReAct 延迟过高,
受控对比需要稳定可复现的推理入口;生产路径仍保留 ReAct + 图谱工具。*