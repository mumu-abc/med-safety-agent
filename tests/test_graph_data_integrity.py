# -*- coding: utf-8 -*-
"""药物知识图谱数据完整性测试（防回归）。

背景（真实踩过的坑）：
    早期数据批次里有 51 条 INTERACTIONS / ALTERNATIVES 引用了当时尚未建库的药物 id
    （如 rifampicin、ketoconazole、MAO_inhibitors）。由于 add_interaction 直接调
    networkx 的 G.add_edge，networkx 会**自动创建没有属性的幽灵节点**，结果是：
      · 交互数虚高（399 里有 43 条是连到幽灵节点的假边）
      · 查询这些"药物"时拿到没有 name / category / 副作用的空 dict
      · 全程没有任何报错，静默失败

修复方式：
    1. add_interaction / add_alternative 遇到未入图的药物直接跳过并 warning
    2. drug_data 补齐缺失药物节点 + id 别名重映射
    3. 新增 validate_data() 校验器 + 本测试文件守住回归
"""
import pytest

from app.graph import drug_data
from app.graph.drug_data import ALTERNATIVES, DRUGS, INTERACTIONS, validate_data


def test_no_dangling_reference():
    """交互/替代关系不得引用不存在的药物 id。"""
    result = validate_data()
    assert result["dangling"] == {}, (
        f"存在悬挂引用（这些药物未建库）: {result['dangling']}"
    )


def test_validate_data_strict_mode():
    """strict=True 时，健康数据不应抛异常。"""
    validate_data(strict=True)  # 不抛即通过


def test_graph_has_no_phantom_nodes():
    """图谱中不得存在"有边相连但没有 drug 标记"的幽灵节点。"""
    from app.graph.drug_graph import get_graph

    G = get_graph()
    phantoms = [n for n, d in G.nodes(data=True) if not d.get("drug")]
    assert phantoms == [], f"发现幽灵节点: {phantoms}"


def test_no_duplicate_drug_id():
    """药物 id 必须唯一——模块加载时已去重，这里守住回归。"""
    seen = set()
    dup = set()
    for d in DRUGS:
        if d["id"] in seen:
            dup.add(d["id"])
        seen.add(d["id"])
    assert dup == set(), f"重复的药物 id: {sorted(dup)}"
    # 去重后长度应与唯一 id 数一致
    assert len(DRUGS) == len(seen)


def test_interaction_severity_legal():
    """严重度字段必须是约定枚举值，避免下游按等级过滤时失效。"""
    legal = {"critical", "high", "medium", "low"}
    bad = [
        (a, b, sev) for a, b, sev, _m in INTERACTIONS if sev not in legal
    ]
    assert bad == [], f"非法 severity（约定为 {legal}）: {bad[:20]}"


def test_every_drug_has_required_fields():
    """每个药物至少要有 id / name / category，否则前端会显示空白。"""
    missing = [
        d["id"] for d in DRUGS
        if not d.get("id") or not d.get("name") or not d.get("category")
    ]
    assert missing == [], f"缺少必填字段的药物: {missing}"


def test_rebuild_produces_consistent_graph():
    """重建后：药物数与去重 id 数一致，交互数与有效去重交互数一致。"""
    expected_drugs = len({d["id"] for d in DRUGS})
    expected_pairs = len({
        tuple(sorted((a, b)))
        for a, b, _s, _m in INTERACTIONS
        if a in {d["id"] for d in DRUGS} and b in {d["id"] for d in DRUGS}
    })

    result = drug_data.build_graph_from_data()
    assert result["dangling_count"] == 0
    assert result["phantom_nodes"] == []
    assert result["drugs"] == expected_drugs
    assert result["interactions"] == expected_pairs


def test_alias_remap_applied():
    """id 别名必须已被重映射，原始别名不应再出现在数据里。"""
    idset = {d["id"] for d in DRUGS}
    for alias, canonical in drug_data._ID_ALIAS.items():
        assert canonical in idset, f"别名目标 {canonical} 不在药物库中"
        for a, b, _s, _m in INTERACTIONS:
            assert alias not in (a, b), (
                f"交互中仍残留未映射的别名 {alias}: {a} <-> {b}"
            )
        for a, b, _r in ALTERNATIVES:
            assert alias not in (a, b), (
                f"替代关系中仍残留未映射的别名 {alias}: {a} <-> {b}"
            )


@pytest.mark.parametrize("drug_id", ["rifampin", "ketoconazole", "fluvoxamine",
                                     "ritonavir", "dabigatran", "NSAIDs"])
def test_previously_missing_drugs_now_in_graph(drug_id):
    """曾被静默丢弃的关键药物现在必须能在图谱里查到。"""
    from app.graph.drug_graph import get_drug

    drug = get_drug(drug_id)
    assert drug is not None, f"{drug_id} 仍不在图谱中"
    assert drug.get("name"), f"{drug_id} 缺少 name"
    assert drug.get("category"), f"{drug_id} 缺少 category"
