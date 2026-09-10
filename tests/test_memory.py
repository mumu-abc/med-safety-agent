"""
记忆系统测试 — CRUD、检索、反馈提取。
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


@pytest.fixture
def mock_deps(monkeypatch):
    """模拟 embedding 模型和 FAISS 索引"""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(1, 512).astype("float32")
    monkeypatch.setattr("app.memory._get_model", lambda: mock_model)

    mock_index = MagicMock()
    mock_index.ntotal = 0
    mock_index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
    monkeypatch.setattr("app.memory._get_index", lambda: mock_index)
    monkeypatch.setattr("app.memory._save_index", lambda: None)

    # Mock faiss module in case it's imported
    mock_faiss = MagicMock()
    monkeypatch.setitem(__import__('sys').modules, 'faiss', mock_faiss)

    return mock_model, mock_index


def test_add_memory(mock_deps, monkeypatch):
    """添加记忆"""
    from app.memory import add_memory

    mock_conn = MagicMock()
    mock_conn.execute.return_value = None
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    mid = add_memory("华法林+阿司匹林出血风险", memory_type="case", drugs="华法林,阿司匹林", risk_level="high")
    assert len(mid) == 8


def test_retrieve_empty_index(mock_deps, monkeypatch):
    """空索引应返回空列表"""
    from app.memory import retrieve_memories

    mock_index = mock_deps[1]
    mock_index.ntotal = 0
    result = retrieve_memories("任何查询")
    assert result == []


def test_retrieve_with_results(mock_deps, monkeypatch):
    """有记忆时应返回结果"""
    from app.memory import retrieve_memories

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = {
        "id": "mem0001", "content": "华法林出血风险", "memory_type": "case",
        "drugs": "华法林", "risk_level": "high", "tags": "", "embedding_id": 0,
        "created_at": "2026-01-01T00:00:00",
    }
    mock_conn.execute.return_value.fetchall.return_value = []
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    result = retrieve_memories("华法林出血", top_k=3)
    assert isinstance(result, list)


def test_format_memories_empty():
    """空记忆应返回空字符串"""
    from app.memory import format_memories_for_context
    assert format_memories_for_context([]) == ""


def test_format_memories_case():
    """案例记忆格式化"""
    from app.memory import format_memories_for_context
    memories = [{"memory_type": "case", "content": "华法林+阿司匹林出血风险高"}]
    result = format_memories_for_context(memories)
    assert "案例" in result
    assert "华法林" in result


def test_format_memories_feedback():
    """反馈记忆格式化"""
    from app.memory import format_memories_for_context
    memories = [{"memory_type": "feedback", "content": "低分反馈(2/5): 漏检了出血风险"}]
    result = format_memories_for_context(memories)
    assert "反馈" in result


def test_extract_and_save_case(mock_deps, monkeypatch):
    """从审查结果提取案例记忆"""
    from app.memory import extract_and_save_case

    mock_conn = MagicMock()
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    mid = extract_and_save_case("华法林 2.5mg qd", "high", "出血风险", ["华法林"])
    assert len(mid) == 8


def test_extract_memories_from_feedback_low(mock_deps, monkeypatch):
    """低分反馈应保存为记忆"""
    from app.memory import extract_memories_from_feedback

    mock_conn = MagicMock()
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    mid = extract_memories_from_feedback("华法林处方", 2, "漏检了出血风险", "high")
    assert len(mid) == 8


def test_extract_memories_from_feedback_high(mock_deps, monkeypatch):
    """高分反馈应保存为记忆"""
    from app.memory import extract_memories_from_feedback

    mock_conn = MagicMock()
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    mid = extract_memories_from_feedback("安全处方", 5, "检测全面", "safe")
    assert len(mid) == 8


def test_extract_memories_from_feedback_neutral(mock_deps, monkeypatch):
    """中立反馈(3分)也保存为feedback_medium类型"""
    from app.memory import extract_memories_from_feedback

    mock_conn = MagicMock()
    monkeypatch.setattr("app.memory._get_conn", lambda: mock_conn)

    mid = extract_memories_from_feedback("处方", 3, "一般", "medium")
    assert len(mid) == 8


def test_memory_module_imports():
    """记忆模块应能导入"""
    from app.memory import add_memory, retrieve_memories, format_memories_for_context
    assert callable(add_memory)
    assert callable(retrieve_memories)
    assert callable(format_memories_for_context)
