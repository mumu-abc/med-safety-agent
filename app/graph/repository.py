"""药物知识图谱 Repository 抽象层。

设计要点:
1. Repository 模式:将图存储与业务逻辑解耦,当前用 networkx 内存图,
   接口设计兼容 Neo4j(只需实现 GraphRepository 协议即可切换)。
2. 图遍历查询:find_interactions 是图遍历,不是 SQL 查表。
3. 多跳推理:find_shortest_path 发现间接交互链(如 A→B→C)。
"""
from typing import Protocol, abstractmethod
import networkx as nx

from app.graph.drug_graph import (
    get_graph, get_drug_by_name, find_interactions, find_contraindications,
    find_alternatives, find_shortest_path, find_drug_communities,
    analyze_interaction_chain, get_all_drugs, get_stats,
    add_drug, add_interaction, add_contraindication, add_alternative,
)


class GraphRepository(Protocol):
    """药物图谱 Repository 协议(接口)。

    当前由 NetworkXRepository 实现。
    如需切换 Neo4j,只需实现此协议即可,业务代码无需改动。
    """

    @abstractmethod
    def get_drug(self, drug_id: str) -> dict | None: ...

    @abstractmethod
    def find_drug_by_name(self, name: str) -> dict | None: ...

    @abstractmethod
    def find_interactions(self, drug_ids: list[str]) -> list[dict]: ...

    @abstractmethod
    def find_contraindications(self, drug_id: str, conditions: list[str]) -> list[dict]: ...

    @abstractmethod
    def find_alternatives(self, drug_id: str, exclude: list[str] | None = None) -> list[dict]: ...

    @abstractmethod
    def find_shortest_interaction_path(self, drug_a: str, drug_b: str) -> list[dict] | None: ...

    @abstractmethod
    def detect_communities(self) -> list[list[str]]: ...

    @abstractmethod
    def analyze_chain(self, drug_names: list[str]) -> dict: ...

    @abstractmethod
    def get_statistics(self) -> dict: ...


class NetworkXRepository:
    """基于 networkx 的内存图 Repository 实现。

    特点:
    - DiGraph 有向图,支持多种关系类型(INTERACTS_WITH/ALTERNATIVE_OF)
    - 图遍历查询,复杂度 O(V+E)
    - 支持多跳推理、社区发现、环路检测
    - 可序列化为 JSON 持久化

    如需切换 Neo4j:
    class Neo4jRepository:
        def find_interactions(self, drug_ids):
            # MATCH (a:Drug)-[r:INTERACTS_WITH]-(b:Drug)
            # WHERE a.id IN $drug_ids AND b.id IN $drug_ids
            # RETURN a, r, b
    """

    def __init__(self):
        self._graph: nx.DiGraph = get_graph()

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def get_drug(self, drug_id: str) -> dict | None:
        if not self._graph.has_node(drug_id):
            return None
        return {"id": drug_id, **dict(self._graph.nodes[drug_id])}

    def find_drug_by_name(self, name: str) -> dict | None:
        return get_drug_by_name(name)

    def find_interactions(self, drug_ids: list[str]) -> list[dict]:
        return find_interactions(drug_ids)

    def find_contraindications(self, drug_id: str, conditions: list[str]) -> list[dict]:
        return find_contraindications(drug_id, conditions)

    def find_alternatives(self, drug_id: str, exclude: list[str] | None = None) -> list[dict]:
        return find_alternatives(drug_id, exclude)

    def find_shortest_interaction_path(self, drug_a: str, drug_b: str) -> list[dict] | None:
        return find_shortest_path(drug_a, drug_b)

    def detect_communities(self) -> list[list[str]]:
        return find_drug_communities()

    def analyze_chain(self, drug_names: list[str]) -> dict:
        return analyze_interaction_chain(drug_names)

    def get_statistics(self) -> dict:
        return get_stats()

    def get_all_drugs(self) -> list[dict]:
        return get_all_drugs()

    def add_drug(self, drug_id: str, name: str, **kwargs) -> str:
        return add_drug(drug_id, name, **kwargs)

    def add_interaction(self, drug_a: str, drug_b: str, severity: str, mechanism: str) -> None:
        add_interaction(drug_a, drug_b, severity, mechanism)

    def add_contraindication(self, drug_id: str, condition: str, severity: str = "high") -> None:
        add_contraindication(drug_id, condition, severity)

    def add_alternative(self, drug_a: str, drug_b: str, reason: str = "") -> None:
        add_alternative(drug_a, drug_b, reason)


_repo: GraphRepository | None = None


def get_repository() -> GraphRepository:
    """获取 Repository 单例。

    当前返回 NetworkXRepository。
    未来可通过环境变量切换:
        if settings.GRAPH_BACKEND == "neo4j":
            return Neo4jRepository(...)
        return NetworkXRepository()
    """
    global _repo
    if _repo is None:
        _repo = NetworkXRepository()
    return _repo
