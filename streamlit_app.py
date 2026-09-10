"""
智能用药安全审查系统 - Streamlit 前端
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# 严重程度中文映射
SEV_ZH = {"critical": "极高", "high": "高", "medium": "中等", "low": "低", "safe": "安全", "unknown": "未知"}
from app.graph.drug_graph import get_graph, get_stats
from app.workflow import review_prescription, review_prescription_stream, ReviewState
from app.agents.supervisor_agent import review_multi_agent, review_multi_agent_hitl, resume_multi_agent
from app.database import get_db
from app.memory import retrieve_memories, extract_and_save_case, extract_memories_from_feedback, format_memories_for_context

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="智能用药安全审查系统",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 自定义样式
# ============================================================
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #1a1a2e; }
    h1 { color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 10px; }
    h2, h3 { color: #16213e; }
    .risk-critical { background:#dc3545;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px; }
    .risk-high { background:#fd7e14;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px; }
    .risk-medium { background:#ffc107;color:#333;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px; }
    .risk-low { background:#28a745;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px; }
    .risk-safe { background:#6c757d;color:#fff;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px; }
    .drug-tag {
        display:inline-block;background:#e3f2fd;color:#1565c0;
        padding:2px 10px;border-radius:12px;margin:2px 4px;font-size:13px;font-weight:500;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 缓存
# ============================================================
@st.cache_resource
def get_cached_graph():
    return get_graph()

@st.cache_data
def get_interaction_stats():
    return get_stats()

@st.cache_data
def get_all_drug_names():
    G = get_cached_graph()
    return sorted([
        data.get("name", n)
        for n, data in G.nodes(data=True)
        if data.get("drug")
    ])


# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("## 💊 智能用药安全审查")
    st.markdown("---")

    stats = get_interaction_stats()
    st.markdown(f"""
    **知识图谱规模**
    - 📦 药物节点: **{stats['num_drugs']}**
    - ⚠️ 交互关系: **{stats['num_interactions']}**
    """)

    st.markdown("---")
    st.markdown("### 🏗️ 三层安全架构")
    st.markdown("""
    1. **图谱层** — NetworkX 路径推理
    2. **规则层** — 硬编码安全规则
    3. **LLM层** — 大模型临床推理
    """)

    st.markdown("---")
    st.markdown("### 📊 评测指标")
    st.markdown("""
    | 指标 | 值 |
   ------|------|
    | 测试用例 | 77 |
    | F1 Score | 97.9% |
    | 召回率 | 100% |
    """)

    st.markdown("---")
    st.markdown("### ⚙️ 设置")
    show_reasoning = st.checkbox("显示推理过程", value=True)
    show_graph_path = st.checkbox("显示图谱路径", value=True)

    st.markdown("---")
    st.markdown("### 🔒 审查模式")
    review_mode = st.radio(
        "选择审查模式",
        ["自动审查", "HITL人工审核", "多Agent协作"],
        index=0,
        help="HITL模式: 高风险处方暂停等待人工确认\n多Agent模式: Supervisor编排,fan-out并行",
    )

    st.markdown("---")
    st.markdown("### 🧠 记忆系统")
    try:
        db = get_db()
        cursor = db._get_conn().execute("SELECT COUNT(*) FROM memories")
        mem_count = cursor.fetchone()[0]
        st.markdown(f"- 💾 累计记忆: **{mem_count}** 条")
    except Exception:
        st.markdown("- 💾 记忆系统已就绪")

    st.markdown("---")
    st.markdown("### 📊 系统状态")
    try:
        db = get_db()
        recent = db.get_recent_feedback(50)
        if recent:
            avg_score = sum(f["rating"] for f in recent) / len(recent)
            low_count = sum(1 for f in recent if f["rating"] <= 2)
            st.markdown(f"- 📝 反馈记录: **{len(recent)}** 条")
            st.markdown(f"- ⭐ 平均评分: **{avg_score:.1f}** / 5")
            if low_count:
                st.markdown(f"- ⚠️ 低分反馈: **{low_count}** 条")
        else:
            st.markdown("- 📝 暂无反馈记录")
    except Exception:
        st.markdown("- 📝 数据库未初始化")

    st.markdown("---")
    st.caption("Powered by LangChain + LangGraph + NetworkX")


# ============================================================
# 主页面
# ============================================================
st.markdown("# 💊 智能用药安全审查系统")
st.markdown("**三层安全架构 | 知识图谱推理 | LLM 临床推理 | 规则引擎兜底**")
st.markdown("")

# ---- 示例处方 ----
st.markdown("### 📝 输入处方")

EXAMPLES = {
    "高风险：华法林+阿司匹林+布洛芬": """患者: 张某某, 男, 68岁
诊断: 房颤, 冠心病, 骨关节炎
处方:
- 华法林 5mg qd
- 阿司匹林 100mg qd
- 布洛芬 400mg prn""",
    "特殊人群：孕妇+儿童用药": """患者: 李某某, 女, 28岁, 孕20周
诊断: 细菌性尿路感染
处方:
- 左氧氟沙星 500mg qd
- 阿莫西林 500mg tid""",
    "重复用药：两种他汀": """患者: 王某某, 男, 55岁
诊断: 高脂血症, 冠心病
处方:
- 阿托伐他汀 20mg qn
- 瑞舒伐他汀 10mg qn
- 阿司匹林 100mg qd""",
    "中等风险：华法林+胺碘酮": """患者: 赵某某, 女, 72岁
诊断: 房颤, 心力衰竭
处方:
- 华法林 3mg qd
- 胺碘酮 200mg bid
- 地高辛 0.125mg qd""",
    "安全处方：普通感冒": """患者: 刘某某, 女, 30岁
诊断: 上呼吸道感染
处方:
- 阿莫西林 500mg tid
- 氨溴索 30mg tid""",
    "自定义处方": "",
}

selected_example = st.selectbox(
    "选择示例处方，或选择'自定义处方'手动输入：",
    list(EXAMPLES.keys()),
)

if selected_example == "自定义处方":
    prescription_text = st.text_area(
        "请输入处方内容：",
        height=180,
        placeholder="格式示例：\n患者: 张某某, 男, 68岁\n诊断: 房颤\n处方:\n- 华法林 5mg qd\n- 阿司匹林 100mg qd",
    )
else:
    prescription_text = st.text_area(
        "处方内容（可编辑）：",
        value=EXAMPLES[selected_example],
        height=180,
    )

# ---- 审查按钮 ----
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    run_review = st.button("🔍 开始安全审查", type="primary", use_container_width=True)


# ============================================================
# 执行审查
# ============================================================
if run_review and prescription_text.strip():
    st.markdown("---")
    st.markdown("## 🔍 审查结果")

    # 记忆检索：查找历史相似案例
    memories = retrieve_memories(prescription_text[:200], top_k=3)

    # 根据审查模式选择执行方式
    if review_mode == "HITL人工审核":
        progress_bar = st.progress(0, text="HITL模式: 解析处方...")
        result, thread_id, needs_resume = review_multi_agent_hitl(prescription_text)
        progress_bar.progress(100, text="审查完成!")
        if needs_resume:
            st.session_state["hitl_thread_id"] = thread_id
            st.session_state["hitl_result"] = result
        time.sleep(0.3)
        progress_bar.empty()
    elif review_mode == "多Agent协作":
        progress_bar = st.progress(0, text="多Agent模式: Supervisor编排中...")
        result = review_multi_agent(prescription_text)
        progress_bar.progress(100, text="审查完成!")
        time.sleep(0.3)
        progress_bar.empty()
    else:
        # 流式模式:逐步显示真实进度
        status_container = st.status("🔍 正在审查处方...", expanded=True)
        result = None
        step_count = 0
        for update in review_prescription_stream(prescription_text):
            if update["status"] == "running":
                step_count += 1
                status_container.update(label=f"⏳ {update['label']}...", state="running")
            elif update["status"] == "done":
                result = update["result"]
                status_container.update(label="✅ 审查完成!", state="complete")
            elif update["status"] == "error":
                status_container.update(label=f"❌ {update['label']}", state="error")
        status_container.update(expanded=False)

    # 保存结果到 session_state 供展示使用
    st.session_state["review_result"] = result
    st.session_state["review_memories"] = memories

    # 审查完成后提取记忆
    if result:
        risk_assessment_tmp = result.get("risk_assessment")
        overall_risk_tmp = getattr(risk_assessment_tmp, "overall_risk", "unknown") if risk_assessment_tmp else "unknown"
        rule_risks_tmp = result.get("rule_risks", [])
        risk_summary_tmp = "; ".join(r.get("risk", "") for r in rule_risks_tmp[:3]) if rule_risks_tmp else "无风险"
        prescription_tmp = result.get("prescription")
        drug_names_tmp = [d.name for d in prescription_tmp.drugs] if prescription_tmp and hasattr(prescription_tmp, 'drugs') else []
        extract_and_save_case(prescription_text[:200], overall_risk_tmp, risk_summary_tmp, drug_names_tmp)

    # ---- HITL 中断处理 ----
    if review_mode == "HITL人工审核" and st.session_state.get("hitl_thread_id"):
        st.markdown("---")
        st.markdown("### ⏸️ 人工审核中断")
        ra = result.get("risk_assessment")
        if ra:
            st.warning(f"**风险评估完成，总体风险: {SEV_ZH.get(getattr(ra, 'overall_risk', 'unknown'), '未知')}**")
            st.markdown(f"> {getattr(ra, 'summary', '')}")
            if hasattr(ra, 'risks') and ra.risks:
                for r in ra.risks:
                    sev = getattr(r, 'severity', 'medium')
                    icon = {"critical": "🚨", "high": "⚠️", "medium": "⚡"}.get(sev, "ℹ️")
                    st.markdown(f"- {icon} **[{SEV_ZH.get(sev, sev)}]** {getattr(r, 'drug', '')}: {getattr(r, 'description', '')}")

        col_hitl1, col_hitl2 = st.columns(2)
        with col_hitl1:
            if st.button("✅ 批准 — 继续推荐替代方案", type="primary", use_container_width=True):
                with st.spinner("正在恢复审查流程..."):
                    final_result = resume_multi_agent(st.session_state["hitl_thread_id"])
                st.session_state["hitl_final"] = final_result
                del st.session_state["hitl_thread_id"]
                del st.session_state["hitl_result"]
                st.rerun()
        with col_hitl2:
            if st.button("❌ 驳回 — 跳过替代方案", use_container_width=True):
                st.session_state["hitl_final"] = st.session_state["hitl_result"]
                del st.session_state["hitl_thread_id"]
                del st.session_state["hitl_result"]
                st.rerun()

# ---- HITL 恢复后展示最终结果 ----
if st.session_state.get("hitl_final"):
    st.session_state["review_result"] = st.session_state["hitl_final"]
    del st.session_state["hitl_final"]

# ---- 统一展示审查结果 ----
_display_result = st.session_state.get("review_result")
if _display_result:
    memories = st.session_state.get("review_memories", [])
    # ---- 提取结果 ----
    report = _display_result.get("report")
    prescription = _display_result.get("prescription")
    interactions = _display_result.get("interactions", [])
    contraindications = _display_result.get("contraindications", [])
    rule_risks = _display_result.get("rule_risks", [])
    risk_assessment = _display_result.get("risk_assessment")
    alternatives = _display_result.get("alternatives")
    overall_risk = getattr(risk_assessment, "overall_risk", "unknown") if risk_assessment else "unknown"

    # ---- 总体风险概览 ----
    risk_colors = {
        "critical": ("#dc3545", "极高风险", "🚨"),
        "high": ("#fd7e14", "高风险", "⚠️"),
        "medium": ("#ffc107", "中等风险", "⚡"),
        "low": ("#28a745", "低风险", "✅"),
        "safe": ("#6c757d", "安全", "✔️"),
    }
    color, label, icon = risk_colors.get(overall_risk, ("#6c757d", "未知", "❓"))

    st.markdown(f"""
    <div style="background:{color};color:#fff;padding:20px 30px;border-radius:12px;
                display:flex;align-items:center;gap:20px;margin:16px 0;">
        <span style="font-size:48px;">{icon}</span>
        <div>
            <div style="font-size:28px;font-weight:bold;">总体风险等级: {label}</div>
            <div style="font-size:16px;opacity:0.9;">
                检测到 {len(interactions)} 个药物交互, {len(rule_risks)} 条规则风险
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 指标卡片 ----
    col1, col2, col3, col4 = st.columns(4)
    drug_count = len(prescription.drugs) if prescription else 0
    with col1:
        st.metric("药物数量", drug_count)
    with col2:
        st.metric("交互数量", len(interactions))
    with col3:
        st.metric("规则风险", len(rule_risks))
    with col4:
        alt_count = len(alternatives.suggestions) if hasattr(alternatives, 'suggestions') else (len(alternatives.recommendations) if hasattr(alternatives, 'recommendations') else 0)
        st.metric("替代建议", alt_count)

    st.markdown("")

    # ---- 历史相似案例 ----
    if memories:
        with st.expander(f"🧠 发现 {len(memories)} 个相似历史案例", expanded=False):
            for mem in memories:
                score_pct = int(mem["score"] * 100)
                st.markdown(f"- **[{mem.get('memory_type', 'case')}]** {mem.get('content', '')[:120]}... (相似度: {score_pct}%)")

    # ---- Tab 布局 ----
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 审查报告", "⚠️ 药物交互", "📏 规则引擎", "🔄 替代方案", "🧠 推理过程"
    ])

    # ---- Tab 1: 审查报告 ----
    with tab1:
        if report:
            if isinstance(report, str):
                st.markdown(report)
            elif hasattr(report, 'title'):
                st.markdown(f"### {report.title}")
                st.markdown(f"**{report.summary}**")
                st.markdown("")
                if hasattr(report, 'findings') and report.findings:
                    for finding in report.findings:
                        severity_class = f"risk-{finding.severity}"
                        with st.expander(
                            f"{finding.category} | {finding.title} [{SEV_ZH.get(finding.severity, finding.severity)}]",
                            expanded=(finding.severity in ("critical", "high"))
                        ):
                            st.markdown(f'<span class="{severity_class}">{SEV_ZH.get(finding.severity, finding.severity)}</span>',
                                       unsafe_allow_html=True)
                            st.markdown(f"**{finding.title}**")
                            st.markdown(finding.description)
                            if hasattr(finding, 'evidence') and finding.evidence:
                                st.markdown("**证据来源:**")
                                for ev in finding.evidence:
                                    st.markdown(f"- {ev}")
                            if hasattr(finding, 'suggestion') and finding.suggestion:
                                st.info(f"💡 **建议:** {finding.suggestion}")
                else:
                    st.success("✅ 未发现显著用药安全问题")
            else:
                st.markdown(str(report))
        else:
            st.warning("未生成审查报告")

    # ---- Tab 2: 药物交互 ----
    with tab2:
        all_issues = interactions + contraindications
        if all_issues:
            for inter in all_issues:
                drug_a = inter.get("drug_a", inter.get("drug", ""))
                drug_b = inter.get("drug_b", "")
                severity = inter.get("severity", "unknown")
                desc = inter.get("description", inter.get("mechanism", ""))
                severity_class = f"risk-{severity}"

                label_text = f"💊 {drug_a}"
                if drug_b:
                    label_text += f" ↔ {drug_b}"
                label_text += f"  [{SEV_ZH.get(severity, severity)}]"

                with st.expander(label_text, expanded=(severity in ("critical", "high"))):
                    st.markdown(f'<span class="{severity_class}">{SEV_ZH.get(severity, severity)}</span>',
                               unsafe_allow_html=True)
                    if drug_b:
                        st.markdown(f"**{drug_a}** + **{drug_b}**")
                    else:
                        st.markdown(f"**{drug_a}**")
                    st.markdown(desc)
        else:
            st.success("✅ 未检测到药物交互或禁忌")

    # ---- Tab 3: 规则引擎 ----
    with tab3:
        if rule_risks:
            for risk in rule_risks:
                drug = risk.get("drug", "未知")
                rule = risk.get("rule", "unknown")
                severity = risk.get("severity", "medium")
                risk_desc = risk.get("risk", "")
                suggestion = risk.get("suggestion", "")
                sev_color = {
                    'critical': '#dc3545', 'high': '#fd7e14',
                    'medium': '#ffc107', 'low': '#28a745'
                }.get(severity, '#6c757d')
                severity_class = f"risk-{severity}"

                st.markdown(f"""
                <div style="background:#fff;border-left:4px solid {sev_color};
                            padding:12px 16px;margin:8px 0;border-radius:0 8px 8px 0;
                            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <span class="{severity_class}">{SEV_ZH.get(severity, severity)}</span>
                    <b style="margin-left:8px;">{drug}</b> — <code>{rule}</code>
                    <p style="margin:8px 0 0 0;">{risk_desc}</p>
                    {'<p style="color:#0c5460;margin:4px 0 0 0;">💡 ' + suggestion + '</p>' if suggestion else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ 规则引擎未发现风险")

    # ---- Tab 4: 替代方案 ----
    with tab4:
        if hasattr(alternatives, 'suggestions') and alternatives.suggestions:
            for rec in alternatives.suggestions:
                st.markdown(f"### 💊 {rec.original_drug} 的替代方案")
                st.markdown(f"**原因:** {rec.reason}")
                cols = st.columns(min(len(rec.alternatives), 3))
                for j, alt in enumerate(rec.alternatives[:3]):
                    with cols[j % 3]:
                        st.markdown(f"""
                        <div style="background:#e8f5e9;padding:16px;border-radius:10px;
                                    border:1px solid #a5d6a7;">
                            <b style="font-size:16px;">{alt.name}</b>
                            <p style="color:#555;margin:8px 0;">{getattr(alt, 'category', '')} — {getattr(alt, 'reason', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("当前处方无需替代方案")

    # ---- Tab 5: 推理过程 ----
    with tab5:
        if show_reasoning:
            st.markdown("### 🧠 Agent 推理过程")

            if prescription:
                with st.expander("📝 阶段1: 处方解析", expanded=False):
                    drugs_data = []
                    for d in prescription.drugs:
                        drugs_data.append({
                            "drug": d.name,
                            "dose": d.dosage,
                            "freq": d.frequency,
                            "duration": getattr(d, 'duration', ''),
                        })
                    st.json({
                        "patient": {
                            "age": prescription.patient.age,
                            "gender": prescription.patient.gender,
                            "conditions": prescription.patient.conditions,
                        },
                        "diagnoses": prescription.diagnosis,
                        "medications": drugs_data,
                    })

            if interactions:
                with st.expander("🔍 阶段2: 交互检测", expanded=False):
                    for inter in interactions:
                        st.markdown(
                            f"- **{inter.get('drug_a','')} ↔ {inter.get('drug_b','')}**: "
                            f"{SEV_ZH.get(inter.get('severity',''), inter.get('severity',''))} — {inter.get('mechanism','')}"
                        )

            if rule_risks:
                with st.expander("📏 阶段3: 规则引擎", expanded=False):
                    for risk in rule_risks:
                        st.markdown(
                            f"- **{risk.get('drug','')}**: {risk.get('risk','')} "
                            f"[{SEV_ZH.get(risk.get('severity',''), risk.get('severity',''))}]"
                        )

            if risk_assessment:
                with st.expander("📊 阶段4: 风险评估", expanded=False):
                    if hasattr(risk_assessment, 'model_dump'):
                        st.json(risk_assessment.model_dump())
                    elif hasattr(risk_assessment, '__dict__'):
                        st.json(risk_assessment.__dict__)
                    else:
                        st.json(str(risk_assessment))

            # 多Agent模式: 显示Agent执行历史
            agent_history = _display_result.get("agent_history", [])
            if agent_history:
                with st.expander("🤖 Agent 执行轨迹", expanded=False):
                    st.markdown("**Supervisor 编排执行路径:**")
                    for i, agent_name in enumerate(agent_history, 1):
                        icon = {"parse": "📝", "detect": "🔍", "rules": "📏", "assess": "📊",
                                "recommend": "💊", "report": "📋"}.get(agent_name, "⚙️")
                        st.markdown(f"{i}. {icon} `{agent_name}`")

    # ---- 用户反馈 ----
    st.markdown("---")
    st.markdown("### 📝 审查反馈")
    st.markdown("您的反馈将帮助系统持续改进")

    fb_col1, fb_col2 = st.columns([1, 2])
    with fb_col1:
        feedback_score = st.slider("审查质量评分", 1, 5, 3, key="fb_score",
                                    help="1=很差 5=很好")
    with fb_col2:
        feedback_comment = st.text_input("补充说明（可选）", key="fb_comment",
                                          placeholder="例如：漏检了XX风险 / 检测很全面")

    if st.button("📤 提交反馈", key="submit_feedback"):
        try:
            db = get_db()
            db.save_feedback(
                case_desc=prescription_text[:200],
                rating=feedback_score,
                comment=feedback_comment,
            )
            # 记忆注入
            extract_memories_from_feedback(
                prescription_text[:200], feedback_score, feedback_comment, overall_risk
            )
            st.success("✅ 感谢反馈！已记录并注入记忆系统")
        except Exception as e:
            st.error(f"反馈保存失败: {e}")

    # ---- 知识图谱可视化 ----
    st.markdown("---")
    st.markdown("### 🕸️ 知识图谱可视化")

    if prescription and prescription.drugs:
        import networkx as nx
        G = get_cached_graph()
        drug_names = [d.name for d in prescription.drugs]

        subgraph_nodes = set()
        for dn in drug_names:
            for node in G.nodes():
                dn_lower = dn.lower()
                node_name = G.nodes[node].get("name", "").lower()
                if dn_lower in node_name or node_name in dn_lower:
                    subgraph_nodes.add(node)
                    for neighbor in G.neighbors(node):
                        subgraph_nodes.add(neighbor)

        if subgraph_nodes:
            subG = G.subgraph(subgraph_nodes)

            try:
                from pyvis.network import Network
                import tempfile

                net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#333")
                net.barnes_hut(gravity=-3000, central_gravity=0.3)

                color_map = {
                    "critical": "#dc3545", "high": "#fd7e14",
                    "medium": "#ffc107", "low": "#28a745",
                }

                for node in subG.nodes():
                    is处方 = any(
                        dn.lower() in G.nodes[node].get("name", "").lower()
                        for dn in drug_names
                    )
                    net.add_node(
                        node,
                        label=G.nodes[node].get("name", node),
                        color="#e94560" if is处方 else "#0f3460",
                        size=30 if is处方 else 15,
                        borderWidth=3 if is处方 else 1,
                    )

                for u, v, data in subG.edges(data=True):
                    rel = data.get("relation", "")
                    if rel == "INTERACTS_WITH":
                        sev = data.get("severity", "medium")
                        net.add_edge(
                            u, v,
                            color=color_map.get(sev, "#999"),
                            width=2 if sev in ("critical", "high") else 1,
                            title=f"{sev}: {data.get('mechanism', '')}",
                        )
                    elif rel == "ALTERNATIVE_OF":
                        net.add_edge(u, v, color="#4caf50", width=1, dashes=True, title="替代药物")

                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.html', delete=False, encoding='utf-8'
                ) as f:
                    net.save_graph(f.name)
                    html_path = f.name

                with open(html_path, 'r', encoding='utf-8') as f:
                    graph_html = f.read()

                st.components.v1.html(graph_html, height=520)
                os.unlink(html_path)

                st.markdown("""
                **图例:**
                🔴 处方中的药物 | 🔵 知识图谱中的相关药物
                🟠 高风险交互 | 🟡 中等风险 | 🟢 替代药物（虚线）
                """)
            except ImportError:
                st.info("安装 pyvis 以启用图谱可视化: `pip install pyvis`")
        else:
            st.info("处方中的药物未在知识图谱中找到")
    else:
        st.info("请输入处方并执行审查以查看图谱可视化")


# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#999;font-size:13px;">
    智能用药安全审查系统 | LangChain + LangGraph + NetworkX | 三层安全架构<br>
    仅供辅助决策，不替代临床药师专业判断
</div>
""", unsafe_allow_html=True)
