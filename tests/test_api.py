"""API 测试(用 TestClient,不需要启动服务器)。"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---- 根路由 ----

def test_api_root():
    r = client.get("/api")
    assert r.status_code == 200
    data = r.json()
    assert "endpoints" in data


# ---- 药物 API ----

def test_list_drugs():
    r = client.get("/api/drugs")
    assert r.status_code == 200
    data = r.json()
    assert "drugs" in data
    assert len(data["drugs"]) > 0


def test_search_drug():
    r = client.get("/api/drugs/search?name=华法林")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "华法林"


def test_drug_stats():
    r = client.get("/api/drugs/stats")
    assert r.status_code == 200
    data = r.json()
    assert "num_drugs" in data
    assert data["num_drugs"] > 200


def test_interactions():
    r = client.post("/api/drugs/interactions", json=["华法林", "阿司匹林"])
    assert r.status_code == 200
    data = r.json()
    assert "interactions" in data


def test_shortest_path():
    r = client.get("/api/drugs/path?drug_a=华法林&drug_b=阿司匹林")
    assert r.status_code == 200


def test_communities():
    r = client.get("/api/drugs/communities")
    assert r.status_code == 200
    data = r.json()
    assert "communities" in data


# ---- 患者 API ----

def test_patients_crud():
    # 列表(初始为空)
    r = client.get("/api/patients")
    assert r.status_code == 200

    # 创建
    r = client.put("/api/patients/test001", json={
        "name": "张三", "age": 65, "gender": "male",
        "conditions": ["高血压"], "allergies": [],
    })
    assert r.status_code == 200

    # 查询
    r = client.get("/api/patients/test001")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "张三"
    assert data["age"] == 65


# ---- 审查 API(mock LLM) ----

def test_review_endpoint_mock(monkeypatch):
    """审查 API 测试(mock LLM,不消耗 token)。"""
    from unittest.mock import MagicMock, patch

    # mock 整个 review_prescription 返回值
    mock_result = MagicMock()
    mock_result.report = "测试报告"
    mock_result.prescription.diagnosis = "高血压"
    mock_result.prescription.drugs = []
    mock_result.prescription.patient.age = 65
    mock_result.prescription.patient.gender = "male"
    mock_result.prescription.patient.conditions = []
    mock_result.prescription.patient.allergies = []
    mock_result.risk_assessment.overall_risk = "low"
    mock_result.interactions = []
    mock_result.rule_risks = []
    mock_result.alternatives = None

    with patch("app.routers.review.review_prescription", return_value=mock_result):
        r = client.post("/api/review", json={"prescription_text": "测试处方"})
        assert r.status_code == 200
        data = r.json()
        assert "report" in data
        assert data["risk_level"] == "low"
