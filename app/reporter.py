"""报告生成模块(P3-27:从 workflow.py 独立出来)。"""

# 中文映射
_LIVER_RENAL_ZH = {"normal": "正常", "mild": "轻度异常", "moderate": "中度异常", "severe": "重度异常", "impaired": "异常", "unknown": "未知"}
_RISK_ZH = {"critical": "极高", "high": "高", "medium": "中等", "low": "低", "safe": "安全", "unknown": "未知"}
_RISK_TYPE_ZH = {"interaction": "药物交互", "contraindication": "禁忌", "rule": "规则", "dose": "剂量", "allergy": "过敏", "pregnancy": "孕期", "organ": "器官功能"}


def generate_report(ctx: dict) -> str:
    """生成可读的审查报告。"""
    lines = []
    lines.append("=" * 50)
    lines.append("📋 用药安全审查报告")
    lines.append("=" * 50)

    # 处方信息
    prescription = ctx.get("prescription")
    if prescription:
        p = prescription
        lines.append(f"\n🏥 诊断: {getattr(p, 'diagnosis', '') or '未提供'}")
        patient = getattr(p, "patient", None)
        if patient:
            lines.append(f"👤 患者: {getattr(patient, 'age', '') or '?'}岁 {getattr(patient, 'gender', '') or '?'}")
            conditions = getattr(patient, "conditions", [])
            if conditions:
                lines.append(f"   疾病: {', '.join(conditions)}")
            allergies = getattr(patient, "allergies", [])
            if allergies:
                lines.append(f"   过敏: {', '.join(allergies)}")
            liver = _LIVER_RENAL_ZH.get(getattr(patient, 'liver_function', 'normal'), '正常')
            renal = _LIVER_RENAL_ZH.get(getattr(patient, 'renal_function', 'normal'), '正常')
            lines.append(f"   肝功能: {liver} | 肾功能: {renal}")

        drugs = getattr(p, "drugs", [])
        lines.append(f"\n💊 处方药物:")
        for d in drugs:
            lines.append(f"   - {d.name} {d.dosage} {d.frequency}")

    # 风险等级
    risk_assessment = ctx.get("risk_assessment")
    if risk_assessment:
        risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "safe": "✅"}
        overall = risk_assessment.overall_risk
        lines.append(f"\n{'=' * 50}")
        lines.append(f"⚠️  总体风险: {risk_emoji.get(overall, '❓')} {_RISK_ZH.get(overall, overall)}")
        lines.append(f"{'=' * 50}")

    # 相互作用
    interactions = ctx.get("interactions", [])
    if interactions:
        lines.append(f"\n⚡ 药物相互作用 ({len(interactions)}项):")
        for it in interactions:
            sev = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            lines.append(f"   {sev.get(it['severity'], '❓')} {it['drug_a']} + {it['drug_b']}")
            sev_zh = _RISK_ZH.get(it['severity'], it['severity'])
            lines.append(f"      严重程度: {sev_zh} | {it['mechanism']}")

    # 禁忌症
    contraindications = ctx.get("contraindications", [])
    if contraindications:
        lines.append(f"\n🚫 禁忌症匹配 ({len(contraindications)}项):")
        for ct in contraindications:
            lines.append(f"   🔴 {ct['drug']}: {ct['condition']}")

    # 规则引擎风险
    rule_risks = ctx.get("rule_risks", [])
    if rule_risks:
        lines.append(f"\n📐 规则引擎检测 ({len(rule_risks)}项):")
        for rr in rule_risks:
            sev = {"critical": "🔴", "high": "🟠", "medium": "🟡"}
            lines.append(f"   {sev.get(rr['severity'], '❓')} [{rr['rule']}] {rr['drug']}: {rr['risk']}")
            if rr.get("suggestion"):
                lines.append(f"      建议: {rr['suggestion']}")

    # 风险详情
    if risk_assessment and risk_assessment.risks:
        lines.append(f"\n📊 风险评估详情 ({len(risk_assessment.risks)}项):")
        for r in risk_assessment.risks:
            sev = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            src = "📐" if r.source == "rule" else "🤖"
            risk_type_zh = _RISK_TYPE_ZH.get(r.risk_type, r.risk_type)
            lines.append(f"   {sev.get(r.severity, '❓')} {src} [{risk_type_zh}] {r.drug}: {r.description}")
            if r.suggestion:
                lines.append(f"      建议: {r.suggestion}")

    # 替代方案
    alternatives = ctx.get("alternatives")
    if alternatives and alternatives.suggestions:
        lines.append(f"\n💡 替代方案建议:")
        for s in alternatives.suggestions:
            lines.append(f"   替换 {s.original_drug}:")
            if s.alternatives:
                for alt in s.alternatives:
                    lines.append(f"   → {alt.name} ({alt.category}) — {alt.reason}")
            else:
                lines.append(f"   → {s.reason}")

    # 总结
    if risk_assessment:
        lines.append(f"\n{'=' * 50}")
        lines.append(f"📝 总结: {risk_assessment.summary}")
        lines.append(f"{'=' * 50}")

    return "\n".join(lines)
