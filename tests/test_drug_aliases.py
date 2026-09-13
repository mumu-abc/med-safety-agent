"""药物别名解析测试。"""
from app.graph.drug_data import build_graph_from_data
from app.graph.drug_graph import get_drug_by_name


def test_brand_and_alias_resolution():
    build_graph_from_data()
    assert get_drug_by_name("波立维")["id"] == "clopidogrel"
    assert get_drug_by_name("拜阿司匹灵")["id"] == "aspirin"
    assert get_drug_by_name("芬必得")["id"] == "ibuprofen"
    assert get_drug_by_name("立普妥")["id"] == "atorvastatin"
    assert get_drug_by_name("强的松")["id"] == "prednisone"
    assert get_drug_by_name("锂盐")["id"] == "lithium"
    assert get_drug_by_name("碳酸锂")["id"] == "lithium"


def test_exact_generic_still_works():
    build_graph_from_data()
    assert get_drug_by_name("华法林")["id"] == "warfarin"
    assert get_drug_by_name("阿司匹林")["id"] == "aspirin"
