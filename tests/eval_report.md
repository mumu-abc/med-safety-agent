# 用药安全审查系统 — 评测报告

> ⚠️ **历史存档：早期 14 用例的冒烟评测，不是当前评测口径。**
> 当前评测见项目根目录 `EVAL_REPORT.md`（主集 191 样本，图谱+规则 F1 = **94.8%**）；
> 本文件的 F1 0.828 是 14 用例阶段的中间结果，**不要对外引用**。

## 测试用例: 14 个

## 整体指标

| 指标 | 规则引擎 | 图谱+规则 | 提升 |
|------|---------|----------|------|
| PRECISION | 1.000 | 1.000 | +0.000 |
| RECALL | 0.118 | 0.706 | +0.588 |
| F1 | 0.211 | 0.828 | +0.617 |

## 逐用例结果

| 用例 | 预期 | 规则检测 | 图谱检测 | 规则命中 | 图谱命中 |
|------|------|---------|---------|---------|---------|
| 华法林+阿司匹林: 出血风险 | interaction | 无 | interaction | ❌ | ✅ |
| 二甲双胍+肾功能不全: 乳酸酸中毒 | contraindication | 无 | 无 | ❌ | ❌ |
| 曲马多+SSRI: 5-HT综合征 | interaction | 无 | interaction | ❌ | ✅ |
| 庆大霉素+肾功能不全: 肾毒性 | contraindication | 无 | 无 | ❌ | ❌ |
| 华法林+妊娠: 致畸 | contraindication | 无 | 无 | ❌ | ❌ |
| 多重用药: 4种抗凝/抗血小板 | interaction, rule | rule | rule, interaction | ❌ | ✅ |
| 碳酸锂+NSAIDs: 血锂升高 | interaction | 无 | interaction | ❌ | ✅ |
| 吉非罗齐+他汀: 横纹肌溶解 | interaction | 无 | interaction | ❌ | ✅ |
| 乙醇+苯二氮卓: 呼吸抑制 | interaction | 无 | interaction | ❌ | ✅ |
| 保钾利尿剂+钾补充: 高钾血症 | interaction, rule | 无 | interaction | ❌ | ❌ |
| 抗酸药+左甲状腺素: 吸收减少 | interaction | 无 | interaction | ❌ | ✅ |
| 西咪替丁+华法林: CYP抑制增强抗凝 | interaction | 无 | interaction | ❌ | ✅ |
| 单一安全药物: 无风险 | 无 | 无 | 无 | ✅ | ✅ |
| 老年心衰多重用药: 多种风险叠加 | interaction, rule, contraindication | rule | rule, interaction | ❌ | ❌ |