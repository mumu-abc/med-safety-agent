"""药物知识图谱:NetworkX 图存储 + 查询。

面试要点:
1. 药物-药物相互作用图,不是文本检索,是结构化图遍历。
2. 关系类型丰富:相互作用/禁忌/代谢途径/替代药物。
3. 查询不依赖LLM,直接图遍历,确保可靠性。
"""
import json
from pathlib import Path
import networkx as nx
from app.config import settings

_graph: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    global _graph
    if _graph is None:
        _graph = _load_graph()
    return _graph


def _load_graph() -> nx.DiGraph:
    p = Path(settings.graph_path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        G = nx.DiGraph()
        for node in data.get("nodes", []):
            G.add_node(node["id"], **node.get("attrs", {}))
        for edge in data.get("edges", []):
            G.add_edge(edge["source"], edge["target"], **edge.get("attrs", {}))
        return G
    return nx.DiGraph()


def save_graph():
    G = get_graph()
    p = Path(settings.graph_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": [{"id": n, "attrs": dict(G.nodes[n])} for n in G.nodes],
        "edges": [{"source": u, "target": v, "attrs": dict(G[u][v])} for u, v in G.edges],
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- 药物操作 ----

def add_drug(drug_id: str, name: str, category: str = "",
             generic_name: str = "", contraindications: list[str] | None = None,
             side_effects: list[str] | None = None, metabolism: str = "") -> str:
    G = get_graph()
    attrs = {"name": name, "category": category, "drug": True}
    if generic_name:
        attrs["generic_name"] = generic_name
    if contraindications:
        attrs["contraindications"] = contraindications
    if side_effects:
        attrs["side_effects"] = side_effects
    if metabolism:
        attrs["metabolism"] = metabolism
    G.add_node(drug_id, **attrs)
    return drug_id


def add_interaction(drug_a: str, drug_b: str, severity: str,
                    mechanism: str, bidirectional: bool = True) -> None:
    """添加药物相互作用。"""
    G = get_graph()
    G.add_edge(drug_a, drug_b, relation="INTERACTS_WITH",
               severity=severity, mechanism=mechanism)
    if bidirectional:
        G.add_edge(drug_b, drug_a, relation="INTERACTS_WITH",
                   severity=severity, mechanism=mechanism)


def add_contraindication(drug_id: str, condition: str, severity: str = "high") -> None:
    """添加禁忌症(作为节点属性追加,severity存在独立字段中)。"""
    G = get_graph()
    if G.has_node(drug_id):
        # P1-10修复:severity存入独立的contraindication_severities字段
        contras = G.nodes[drug_id].get("contraindications", [])
        if condition not in contras:
            contras.append(condition)
            G.nodes[drug_id]["contraindications"] = contras
        # severity独立存储,避免破坏现有纯字符串格式
        sev_map = G.nodes[drug_id].get("_contra_severity", {})
        sev_map[condition] = severity
        G.nodes[drug_id]["_contra_severity"] = sev_map


def add_alternative(drug_a: str, drug_b: str, reason: str = "") -> None:
    G = get_graph()
    G.add_edge(drug_a, drug_b, relation="ALTERNATIVE_OF", reason=reason)
    G.add_edge(drug_b, drug_a, relation="ALTERNATIVE_OF", reason=reason)


# ---- 查询 ----

def get_drug(drug_id: str) -> dict | None:
    G = get_graph()
    if not G.has_node(drug_id):
        return None
    return {"id": drug_id, **dict(G.nodes[drug_id])}


# 常见商品名/别名/英文名 → 优先尝试的检索词
# 用于图谱直查兜底;LLM 解析层仍可做更开放的归一
DRUG_ALIASES: dict[str, list[str]] = {
    "波立维": ["氯吡格雷", "clopidogrel"],
    "拜阿司匹灵": ["阿司匹林", "aspirin"],
    "芬必得": ["布洛芬", "ibuprofen"],
    "立普妥": ["阿托伐他汀", "atorvastatin"],
    "强的松": ["泼尼松", "prednisone"],
    "锂盐": ["碳酸锂", "lithium"],
    "苯妥英钠": ["苯妥英", "phenytoin"],
    "心痛定": ["硝苯地平", "nifedipine"],
    "开博通": ["卡托普利", "captopril"],
    "倍他乐克": ["美托洛尔", "metoprolol"],
    "络活喜": ["氨氯地平", "amlodipine"],
    "代文": ["缬沙坦", "valsartan"],
    "蒙诺": ["依那普利", "enalapril"],
    "可乐定": ["可乐定", "clonidine"],
    "苯妥英": ["苯妥英钠", "phenytoin"],
    "苯妥英钠": ["苯妥英钠", "phenytoin"],
}


def get_drug_by_name(name: str) -> dict | None:
    """按名称模糊查找药物。支持常见商品名/别名映射。"""
    G = get_graph()
    raw = (name or "").strip()
    name_lower = raw.lower()

    candidates = [raw]
    for alias, targets in DRUG_ALIASES.items():
        if alias.lower() in name_lower or name_lower in alias.lower():
            candidates.extend(targets)
    # 直接别名表命中
    if raw in DRUG_ALIASES:
        candidates.extend(DRUG_ALIASES[raw])

    for cand in candidates:
        cand_l = cand.strip().lower()
        if not cand_l:
            continue
        for n, data in G.nodes(data=True):
            if not data.get("drug"):
                continue
            drug_name = data.get("name", "").lower()
            generic = data.get("generic_name", "").lower()
            if cand_l == drug_name or cand_l == n.lower():
                return {"id": n, **data}
            if drug_name and (cand_l in drug_name or drug_name in cand_l):
                return {"id": n, **data}
            if generic and (cand_l in generic or generic in cand_l):
                return {"id": n, **data}
    return None


def find_interactions(drug_ids: list[str]) -> list[dict]:
    """查找药物列表中所有两两相互作用。"""
    G = get_graph()
    interactions = []
    seen = set()
    for i, a in enumerate(drug_ids):
        for b in drug_ids[i + 1:]:
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            # 检查两个方向
            for src, dst in [(a, b), (b, a)]:
                if G.has_edge(src, dst):
                    edge = G[src][dst]
                    if edge.get("relation") == "INTERACTS_WITH":
                        seen.add(key)
                        drug_a_data = G.nodes[a] if G.has_node(a) else {}
                        drug_b_data = G.nodes[b] if G.has_node(b) else {}
                        interactions.append({
                            "drug_a": drug_a_data.get("name", a),
                            "drug_b": drug_b_data.get("name", b),
                            "severity": edge.get("severity", "unknown"),
                            "mechanism": edge.get("mechanism", ""),
                        })
                        break
    return interactions


def find_contraindications(drug_id: str, patient_conditions: list[str]) -> list[dict]:
    """检查药物禁忌症与患者状况的匹配。

    P1-11修复:不再用简单子串匹配(会导致"肾"匹配"肝肾功能不全"等假阳性)。
    改为关键词归一化+最小长度要求。
    """
    G = get_graph()
    if not G.has_node(drug_id):
        return []
    drug_data = G.nodes[drug_id]
    contras = drug_data.get("contraindications", [])
    drug_name = drug_data.get("name", drug_id)

    # 关键词归一化:将常见表述映射到标准关键词
    _NORMALIZE = {
        "肾": "肾功能不全", "肾功能": "肾功能不全", "肾功能不全": "肾功能不全",
        "肝": "肝功能不全", "肝功能": "肝功能不全", "肝功能不全": "肝功能不全",
        "肝病": "肝功能不全", "严重肝病": "严重肝功能不全",
        "怀孕": "孕期", "妊娠": "孕期", "孕妇": "孕期",
        "出血": "活动性出血", "溃疡": "消化道溃疡",
    }

    def _normalize(term: str) -> str:
        t = term.strip().lower()
        return _NORMALIZE.get(t, t)

    matches = []
    seen = set()
    for condition in patient_conditions:
        cond_norm = _normalize(condition)
        for contra in contras:
            contra_norm = _normalize(contra)
            # 精确匹配 或 归一化后相等
            exact = condition.lower() == contra.lower()
            normalized = cond_norm == contra_norm
            # 双向子串匹配(但要求最短一方>=4字符,避免"肾"="肝肾"假阳性)
            if not exact and not normalized:
                shorter = min(len(condition), len(contra))
                if shorter < 4:
                    continue
                substring = (condition.lower() in contra.lower() or
                             contra.lower() in condition.lower())
            else:
                substring = False
            if exact or normalized or substring:
                key = (drug_id, condition, contra)
                if key not in seen:
                    seen.add(key)
                    # P1-10:优先从_severity映射读severity
                    sev_map = drug_data.get("_contra_severity", {})
                    sev = sev_map.get(contra, "critical")
                    matches.append({
                        "drug": drug_name,
                        "condition": condition,
                        "contraindication": contra,
                        "severity": sev,
                    })
    return matches


def find_alternatives(drug_id: str, exclude_ids: list[str] | None = None) -> list[dict]:
    """查找替代药物。"""
    G = get_graph()
    if not G.has_node(drug_id):
        return []
    exclude = set(exclude_ids or [])
    exclude.add(drug_id)

    alternatives = []
    for _, target, data in G.edges(drug_id, data=True):
        if data.get("relation") == "ALTERNATIVE_OF" and target not in exclude:
            alt_data = G.nodes[target]
            alternatives.append({
                "id": target,
                "name": alt_data.get("name", target),
                "category": alt_data.get("category", ""),
                "reason": data.get("reason", ""),
            })
    return alternatives


def get_all_drugs() -> list[dict]:
    """获取所有药物列表。"""
    G = get_graph()
    drugs = []
    for n, data in G.nodes(data=True):
        if data.get("drug"):
            drugs.append({"id": n, **data})
    return drugs


def get_all_interactions() -> list[dict]:
    """获取图谱中所有药物相互作用(全量)。"""
    G = get_graph()
    interactions = []
    for u, v, data in G.edges(data=True):
        if data.get("relation") == "INTERACTS_WITH":
            a = G.nodes[u] if G.has_node(u) else {}
            b = G.nodes[v] if G.has_node(v) else {}
            interactions.append({
                "drug_a": a.get("name", u),
                "drug_b": b.get("name", v),
                "severity": data.get("severity", "unknown"),
                "mechanism": data.get("mechanism", ""),
            })
    return interactions


def get_stats() -> dict:
    G = get_graph()
    drug_count = sum(1 for _, d in G.nodes(data=True) if d.get("drug"))
    interaction_count = sum(1 for _, _, d in G.edges(data=True)
                           if d.get("relation") == "INTERACTS_WITH")
    # 统计安全规则数量
    try:
        from app.rules.safety_rules import run_all_rules
        rule_count = 9  # check_age/pregnancy/renal/hepatic/allergies/qt/bleeding/cns/serotonin
    except Exception:
        rule_count = 0
    return {
        "num_drugs": drug_count,
        "num_interactions": interaction_count // 2,  # 双向边算一条
        "categories": _count_attr(G, "category"),
        "rule_count": rule_count,
    }


# ---- 图算法(面试加分项) ----

def find_shortest_path(drug_a: str, drug_b: str) -> list[dict] | None:
    """查找两个药物之间的最短交互路径(多跳推理)。

    例如:华法林 → 阿司匹林 → 布洛芬,说明三者存在交互链。
    这是知识图谱相对于 SQL 查表的核心优势——发现间接关系。
    """
    G = get_graph()
    a_data = get_drug_by_name(drug_a)
    b_data = get_drug_by_name(drug_b)
    if not a_data or not b_data:
        return None

    # 只考虑 INTERACTS_WITH 关系的子图
    interaction_graph = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        if data.get("relation") == "INTERACTS_WITH":
            interaction_graph.add_edge(u, v, **data)

    try:
        path = nx.shortest_path(interaction_graph, a_data["id"], b_data["id"])
        result = []
        for i in range(len(path) - 1):
            node_data = G.nodes[path[i]]
            edge_data = G[path[i]][path[i + 1]]
            result.append({
                "drug": node_data.get("name", path[i]),
                "next": G.nodes[path[i + 1]].get("name", path[i + 1]),
                "severity": edge_data.get("severity", "unknown"),
                "mechanism": edge_data.get("mechanism", ""),
            })
        # 加上最后一个节点
        result.append({"drug": G.nodes[path[-1]].get("name", path[-1]), "next": None})
        return result
    except nx.NetworkXNoPath:
        return None


def find_drug_communities() -> list[list[str]]:
    """基于药物交互关系进行社区发现。

    将交互频繁的药物聚为一类,可发现"药物簇"(如抗凝药群、NSAIDs群)。
    面试时可展示:同一社区内的药物交互密集,跨社区交互稀疏。
    """
    G = get_graph()
    # 只取 INTERACTS_WITH 的无向子图
    undirected = nx.Graph()
    for u, v, data in G.edges(data=True):
        if data.get("relation") == "INTERACTS_WITH":
            undirected.add_edge(u, v)

    if len(undirected.nodes) < 2:
        return []

    # 用 Louvain 社区发现(需 networkx>=2.8)
    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(undirected, seed=42)
    except ImportError:
        # fallback: 连通分量
        communities = list(nx.connected_components(undirected))

    result = []
    for comm in communities:
        drug_names = []
        for node in comm:
            if G.has_node(node) and G.nodes[node].get("drug"):
                drug_names.append(G.nodes[node].get("name", node))
        if drug_names:
            result.append(drug_names)
    return result


def analyze_interaction_chain(drug_names: list[str]) -> dict:
    """分析多药联用的交互链。

    不只是两两交互,还分析:
    - 是否存在共同代谢途径冲突
    - 交互是否形成闭环(A→B→C→A)
    - 最长交互链路径

    这是"知识图谱推理"区别于"SQL查表"的核心能力。
    """
    G = get_graph()
    ids = []
    for name in drug_names:
        d = get_drug_by_name(name)
        if d:
            ids.append(d["id"])

    if len(ids) < 2:
        return {"chain_length": 0, "cycles": [], "metabolism_conflicts": []}

    # 1. 代谢途径冲突分析
    metabolism_map: dict[str, list[str]] = {}
    for drug_id in ids:
        if G.has_node(drug_id):
            met = G.nodes[drug_id].get("metabolism", "")
            drug_name = G.nodes[drug_id].get("name", drug_id)
            for enzyme in met.split("/"):
                enzyme = enzyme.strip()
                if enzyme and enzyme not in ("肾脏排泄", "肝脏代谢", "不吸收", "不代谢"):
                    metabolism_map.setdefault(enzyme, []).append(drug_name)

    metabolism_conflicts = []
    for enzyme, drugs in metabolism_map.items():
        if len(drugs) >= 2:
            metabolism_conflicts.append({
                "enzyme": enzyme,
                "drugs": drugs,
                "risk": f"多药竞争{enzyme}代谢,可能互相影响血药浓度",
            })

    # 2. 交互子图中的环路检测
    interaction_sub = nx.DiGraph()
    for a in ids:
        for b in ids:
            if a != b and G.has_edge(a, b):
                edge = G[a][b]
                if edge.get("relation") == "INTERACTS_WITH":
                    interaction_sub.add_edge(a, b, **edge)

    cycles = []
    try:
        for cycle in nx.simple_cycles(interaction_sub):
            if len(cycle) >= 3:  # 至少3个节点才算有意义的环
                cycle_names = [G.nodes[n].get("name", n) for n in cycle]
                cycles.append(cycle_names)
    except Exception:
        pass

    # 3. 最长交互链
    longest_path = 0
    for a in ids:
        for b in ids:
            if a != b:
                try:
                    path_len = nx.shortest_path_length(interaction_sub, a, b)
                    longest_path = max(longest_path, path_len)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

    return {
        "chain_length": longest_path,
        "cycles": cycles,
        "metabolism_conflicts": metabolism_conflicts,
        "interaction_density": nx.density(interaction_sub) if len(interaction_sub) > 0 else 0,
    }


def _count_attr(G: nx.DiGraph, attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, data in G.nodes(data=True):
        if not data.get("drug"):
            continue
        val = data.get(attr, "unknown")
        if val:
            counts[val] = counts.get(val, 0) + 1
    return counts
