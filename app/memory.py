"""
处方审查记忆系统 — 存储历史审查案例，相似处方自动参考。

记忆类型：
  - case: 审查案例（处方 + 风险结果 + 替代方案）
  - feedback: 用户反馈（评分 + 评论）
  - preference: 用户偏好（药师习惯）

存储：
  - SQLite memories 表存原始文本 + 元数据
  - FAISS 索引存向量（复用 bge-small-zh-v1.5）
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── 全局单例 ──────────────────────────────────────────────
_model = None
_index = None
_memory_dim = 512


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    return _model


def _get_index():
    global _index
    if _index is not None:
        return _index

    import faiss
    from pathlib import Path
    index_path = Path(__file__).resolve().parent.parent / "data" / "memory_index" / "review_memory.faiss"
    if index_path.exists():
        try:
            _index = faiss.deserialize_index(np.frombuffer(index_path.read_bytes(), dtype=np.uint8))
            logger.info(f"记忆索引已加载: {_index.ntotal} 条向量")
        except Exception as e:
            logger.warning(f"记忆索引加载失败: {e}")
            _index = faiss.IndexFlatIP(_memory_dim)
    else:
        _index = faiss.IndexFlatIP(_memory_dim)
    return _index


def _save_index():
    import faiss
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "data" / "memory_index" / "review_memory.faiss"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(faiss.serialize_index(_get_index()))


# ── SQLite 连接单例 ────────────────────────────────────────
_conn = None


def _get_conn():
    """获取 SQLite 连接(模块级单例,避免重复创建)。"""
    global _conn
    if _conn is not None:
        return _conn
    from app.database import DB_PATH
    import sqlite3
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            drugs TEXT,
            risk_level TEXT,
            tags TEXT,
            embedding_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    _conn.commit()
    return _conn


# ── 记忆 CRUD ─────────────────────────────────────────────

def add_memory(
    content: str,
    memory_type: str = "case",
    drugs: str = "",
    risk_level: str = "",
    tags: str = "",
) -> str:
    """存储一条记忆并建立向量索引。"""
    import faiss

    memory_id = uuid.uuid4().hex[:8]
    model = _get_model()
    vec = model.encode([content], normalize_embeddings=True).astype("float32")
    index = _get_index()
    embedding_id = index.ntotal
    index.add(vec)
    _save_index()

    conn = _get_conn()
    conn.execute(
        "INSERT INTO memories (id, content, memory_type, drugs, risk_level, tags, embedding_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (memory_id, content, memory_type, drugs, risk_level, tags, embedding_id, datetime.now().isoformat()),
    )
    conn.commit()

    logger.info(f"💾 新增记忆 [{memory_type}]: {content[:60]}...")
    return memory_id


def retrieve_memories(
    query: str,
    top_k: int = 3,
    memory_type: Optional[str] = None,
) -> list[dict]:
    """语义检索相关记忆。"""
    index = _get_index()
    if index.ntotal == 0:
        return []

    model = _get_model()
    query_vec = model.encode([query], normalize_embeddings=True).astype("float32")

    search_k = min(top_k * 3, index.ntotal)
    scores, indices = index.search(query_vec, search_k)

    conn = _get_conn()
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        row = conn.execute("SELECT * FROM memories WHERE embedding_id = ?", (int(idx),)).fetchone()
        if not row:
            continue
        mem = dict(row)
        if memory_type and mem["memory_type"] != memory_type:
            continue
        mem["score"] = round(float(score), 4)
        results.append(mem)
        if len(results) >= top_k:
            break
    return results


def extract_and_save_case(
    prescription_text: str,
    risk_level: str,
    report_summary: str,
    drugs: list[str],
) -> str:
    """从审查结果中提取并保存案例记忆。"""
    content = (
        f"处方: {prescription_text[:200]}\n"
        f"风险等级: {risk_level}\n"
        f"结论: {report_summary[:200]}"
    )
    return add_memory(
        content=content,
        memory_type="case",
        drugs=",".join(drugs),
        risk_level=risk_level,
    )


def format_memories_for_context(memories: list[dict]) -> str:
    """将记忆格式化为 Agent 可读的上下文。"""
    if not memories:
        return ""

    lines = ["【历史审查参考】"]
    for m in memories:
        if m["memory_type"] == "case":
            lines.append(f"- [案例] {m['content'][:150]}")
        elif m["memory_type"] == "feedback":
            lines.append(f"- [反馈] {m['content'][:150]}")
    return "\n".join(lines)


def extract_memories_from_feedback(
    prescription_text: str,
    rating: int,
    comment: str,
    risk_level: str,
) -> str:
    """从用户反馈中提取记忆。"""
    if rating <= 3:
        content = f"低分反馈({rating}/5): {prescription_text[:100]}... 原因: {comment}"
    elif rating >= 4:
        content = f"高分反馈({rating}/5): {prescription_text[:100]}... 好评: {comment}"
    else:
        return ""

    return add_memory(content=content, memory_type="feedback", risk_level=risk_level)
