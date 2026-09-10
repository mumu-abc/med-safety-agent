"""药物知识图谱可视化浏览器。

功能:
- 搜索任意药物
- 查看其直接关系（交互、禁忌、代谢途径）
- 点击邻居节点继续探索
- 颜色区分: 红色=高危交互, 橙色=中等, 绿色=安全, 蓝色=代谢途径
"""
import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

from app.graph.drug_graph import get_graph, get_drug_by_name

# ---- 页面配置 ----
st.set_page_config(
    page_title="药物知识图谱浏览器",
    page_icon="🕸️",
    layout="wide",
)

st.title("🕸️ 药物知识图谱浏览器")
st.caption("搜索药物 → 查看关系 → 点击探索")

# ---- 颜色映射 ----
SEVERITY_COLORS = {
    "critical": "#ff4d4f",  # 红色
    "high": "#fa8c16",      # 橙色
    "medium": "#fadb14",    # 黄色
    "low": "#52c41a",       # 绿色
    "safe": "#1890ff",      # 蓝色
}

RELATION_COLORS = {
    "INTERACTS_WITH": "#ff4d4f",
    "CONTRAINDICATED": "#ff4d4f",
    "METABOLIZES_BY": "#1890ff",
    "ALTERNATIVE_TO": "#52c41a",
}


@st.cache_data
def get_all_drug_names():
    """获取所有药物名称列表。"""
    G = get_graph()
    names = []
    for node in G.nodes:
        attrs = G.nodes[node]
        name = attrs.get("name", node)
        names.append(name)
    return sorted(set(names))


def get_drug_relations(drug_name: str):
    """获取药物的所有关系。"""
    G = get_graph()

    # 找到药物节点
    drug_id = None
    for node in G.nodes:
        attrs = G.nodes[node]
        if attrs.get("name") == drug_name or node == drug_name:
            drug_id = node
            break

    if not drug_id:
        return None, []

    # 获取所有关系
    relations = []

    # 出边 (该药物 -> 其他)
    for target in G.successors(drug_id):
        edge_data = G[drug_id][target]
        target_name = G.nodes[target].get("name", target)
        relations.append({
            "type": "out",
            "source": drug_name,
            "target": target_name,
            "target_id": target,
            "relation": edge_data.get("relation", "UNKNOWN"),
            "severity": edge_data.get("severity", "unknown"),
            "mechanism": edge_data.get("mechanism", ""),
        })

    # 入边 (其他 -> 该药物)
    for source in G.predecessors(drug_id):
        if source == drug_id:
            continue
        edge_data = G[source][drug_id]
        source_name = G.nodes[source].get("name", source)
        relations.append({
            "type": "in",
            "source": source_name,
            "target": drug_name,
            "source_id": source,
            "relation": edge_data.get("relation", "UNKNOWN"),
            "severity": edge_data.get("severity", "unknown"),
            "mechanism": edge_data.get("mechanism", ""),
        })

    return drug_id, relations


def create_graph_html(center_drug: str, relations: list, depth: int = 1):
    """创建交互式图谱 HTML。"""
    G = get_graph()
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#333333",
        directed=True,
    )

    # 设置物理引擎
    net.barnes_hut(
        gravity=-5000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.05,
    )

    # 添加中心节点
    net.add_node(
        center_drug,
        label=center_drug,
        color="#1890ff",
        size=30,
        font={"size": 16, "bold": True},
        borderWidth=3,
        borderWidthSelected=5,
    )

    # 添加关系节点和边
    added_nodes = {center_drug}

    for rel in relations:
        if rel["type"] == "out":
            neighbor = rel["target"]
        else:
            neighbor = rel["source"]

        if neighbor in added_nodes:
            continue

        # 根据严重程度选颜色
        severity = rel["severity"]
        color = SEVERITY_COLORS.get(severity, "#8c8c8c")

        # 节点大小根据关系数量
        neighbor_relations = len(list(G.neighbors(neighbor))) + len(list(G.predecessors(neighbor)))
        size = min(15 + neighbor_relations * 2, 35)

        net.add_node(
            neighbor,
            label=neighbor,
            color=color,
            size=size,
            font={"size": 12},
            borderWidth=2,
        )
        added_nodes.add(neighbor)

        # 添加边
        relation_label = rel["relation"]
        edge_color = RELATION_COLORS.get(relation_label, "#8c8c8c")

        net.add_edge(
            center_drug if rel["type"] == "out" else neighbor,
            neighbor if rel["type"] == "out" else center_drug,
            color=edge_color,
            width=2,
            title=f"{relation_label}\n{rel['mechanism']}",
            label=relation_label if len(relation_label) < 15 else "",
        )

    # 保存为 HTML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        net.save_graph(f.name)
        with open(f.name, "r", encoding="utf-8") as html_file:
            html_content = html_file.read()
        os.unlink(f.name)

    return html_content


# ---- 侧边栏:搜索 ----
with st.sidebar:
    st.header("🔍 搜索药物")

    all_drugs = get_all_drug_names()
    search_query = st.text_input("输入药物名称", placeholder="如: 华法林")

    # 模糊匹配
    if search_query:
        matches = [d for d in all_drugs if search_query in d]
    else:
        matches = all_drugs[:20]  # 默认显示前20个

    selected_drug = st.selectbox(
        "选择药物",
        options=matches,
        index=0 if matches else None,
    )

    # 统计信息
    st.divider()
    st.metric("图谱规模", f"{len(all_drugs)} 种药物")


# ---- 主区域:图谱可视化 ----
if selected_drug:
    # 获取药物信息
    drug_info = get_drug_by_name(selected_drug)

    # 显示药物详情
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(f"💊 {selected_drug}")

        if drug_info:
            st.write(f"**分类**: {drug_info.get('category', '未知')}")
            st.write(f"**代谢途径**: {drug_info.get('metabolism', '未知')}")

            # 禁忌症
            contras = drug_info.get("contraindications", [])
            if contras:
                st.write("**禁忌症**:")
                for c in contras:
                    st.write(f"  - {c}")

            # 副作用
            sides = drug_info.get("side_effects", [])
            if sides:
                st.write("**常见副作用**:")
                for s in sides[:5]:
                    st.write(f"  - {s}")

    with col2:
        # 获取关系
        drug_id, relations = get_drug_relations(selected_drug)

        if relations:
            # 统计
            interact_count = sum(1 for r in relations if r["relation"] == "INTERACTS_WITH")
            contra_count = sum(1 for r in relations if r["relation"] == "CONTRAINDICATED")

            st.write(f"**关系总数**: {len(relations)} | **药物交互**: {interact_count} | **禁忌症**: {contra_count}")

            # 创建并显示图谱
            html = create_graph_html(selected_drug, relations)
            st.components.v1.html(html, height=620)

            # 图例
            st.markdown("""
            **图例**:
            - 🔵 蓝色 = 当前选中药物
            - 🔴 红色 = 高危/极高危交互
            - 🟠 橙色 = 中等风险
            - 🟢 绿色 = 低风险/安全
            - 箭头方向 = A → B 表示 A 影响 B
            """)
        else:
            st.info("该药物在图谱中没有记录关系")

    # 关系详情列表
    st.divider()
    st.subheader("📋 关系详情")

    if relations:
        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "safe": 4, "unknown": 5}
        sorted_relations = sorted(relations, key=lambda r: severity_order.get(r["severity"], 5))

        for rel in sorted_relations:
            severity = rel["severity"]
            color = SEVERITY_COLORS.get(severity, "#8c8c8c")

            if rel["type"] == "out":
                direction = f"{rel['source']} → {rel['target']}"
            else:
                direction = f"{rel['source']} → {rel['target']}"

            with st.expander(f":{color}[{severity.upper()}] {direction}"):
                st.write(f"**关系类型**: {rel['relation']}")
                st.write(f"**严重程度**: {severity}")
                if rel["mechanism"]:
                    st.write(f"**机制**: {rel['mechanism']}")
    else:
        st.info("没有找到关系数据")

else:
    st.info("👈 请在左侧搜索并选择一个药物")
