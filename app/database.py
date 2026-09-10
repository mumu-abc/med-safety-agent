"""
SQLite 持久化存储 — 评测结果 + 反馈 + 审查缓存。
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "med_safety.db"


class Database:
    """线程安全的 SQLite 数据库管理器"""

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_runs (
                id TEXT PRIMARY KEY,
                run_name TEXT,
                total_cases INTEGER,
                f1 REAL,
                precision_score REAL,
                recall REAL,
                accuracy REAL,
                exact_match INTEGER,
                summary_json TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                description TEXT,
                expected TEXT,
                detected TEXT,
                correct INTEGER,
                created_at TEXT,
                FOREIGN KEY (run_id) REFERENCES eval_runs(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_desc TEXT,
                rating INTEGER,
                comment TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS review_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_hash TEXT UNIQUE NOT NULL,
                prescription_text TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                prescription_text TEXT NOT NULL,
                result_summary TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

    def save_eval_run(self, eval_result: dict) -> str:
        """保存评测结果"""
        run_id = eval_result["run_id"]
        m = eval_result.get("metrics", {})
        conn = self._get_conn()

        conn.execute(
            "INSERT OR REPLACE INTO eval_runs (id, run_name, total_cases, f1, precision_score, recall, accuracy, exact_match, summary_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, eval_result.get("run_name", ""), m.get("total", 0),
             m.get("f1", 0), m.get("precision", 0), m.get("recall", 0), m.get("accuracy", 0),
             m.get("exact_match", 0), json.dumps(eval_result, ensure_ascii=False),
             eval_result.get("timestamp", datetime.now().isoformat())),
        )

        for case in eval_result.get("cases", []):
            conn.execute(
                "INSERT INTO eval_scores (run_id, case_id, description, expected, detected, correct, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, case["case_id"], case.get("desc", ""), case["expected"],
                 case["detected"], int(case["correct"]),
                 eval_result.get("timestamp", datetime.now().isoformat())),
            )

        conn.commit()
        return run_id

    def get_eval_runs(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_eval_run(self, run_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM eval_runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        run = dict(row)
        cases = conn.execute("SELECT * FROM eval_scores WHERE run_id = ? ORDER BY case_id", (run_id,)).fetchall()
        run["cases"] = [dict(r) for r in cases]
        if run.get("summary_json"):
            try:
                full = json.loads(run["summary_json"])
                run["metrics"] = full.get("metrics", {})
            except Exception:
                pass
        return run

    def get_latest_eval_run(self) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def save_feedback(self, case_desc: str, rating: int, comment: str = "") -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO feedback (case_desc, rating, comment, created_at) VALUES (?, ?, ?, ?)",
            (case_desc, rating, comment, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_recent_feedback(self, limit: int = 10) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    # ---- 审查缓存 ----

    @staticmethod
    def _normalize_prescription(text: str) -> str:
        """标准化处方文本，去除不影响语义的差异。"""
        import re
        # 1. 去除首尾空白
        text = text.strip()
        # 2. 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 3. 将多个连续空白（空格、制表符）压缩为单个空格
        text = re.sub(r'[ \t]+', ' ', text)
        # 4. 去除每行首尾空白
        lines = [line.strip() for line in text.split('\n')]
        # 5. 去除空行
        lines = [line for line in lines if line]
        # 6. 排序行（使顺序不同但内容相同的处方产生相同哈希）
        # 注意：这会忽略顺序，如果顺序很重要，可以注释掉这行
        # lines.sort()
        # 7. 统一标点符号（中文逗号、英文逗号、分号等统一为英文）
        normalized = '\n'.join(lines)
        # 统一中文标点为英文标点
        normalized = normalized.replace('，', ',').replace('；', ';').replace('。', '.').replace('：', ':').replace('（', '(').replace('）', ')')
        # 去除标点符号周围的空格
        normalized = re.sub(r'\s*([,;.:\(\)])\s*', r'\1', normalized)
        # 8. 去除多余空格
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.lower()  # 统一大小写

    @staticmethod
    def _hash_prescription(text: str) -> str:
        normalized = Database._normalize_prescription(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def get_cached_review(self, prescription_text: str) -> Optional[dict]:
        """按处方文本查找缓存结果。命中时自动累加hit_count。"""
        h = self._hash_prescription(prescription_text)
        conn = self._get_conn()
        row = conn.execute(
            "SELECT result_json FROM review_cache WHERE prescription_hash = ?", (h,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE review_cache SET hit_count = hit_count + 1 WHERE prescription_hash = ?",
                (h,),
            )
            conn.commit()
            return json.loads(row["result_json"])
        return None

    def save_review_cache(self, prescription_text: str, result: dict) -> None:
        """保存审查结果到缓存(相同处方自动跳过)。"""
        h = self._hash_prescription(prescription_text)
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO review_cache (prescription_hash, prescription_text, result_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (h, prescription_text.strip(), json.dumps(result, ensure_ascii=False, default=str),
             datetime.now().isoformat()),
        )
        conn.commit()

    def get_cache_stats(self) -> dict:
        """返回缓存统计。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(hit_count),0) as total_hits FROM review_cache"
        ).fetchone()
        return {"cached_items": row["count"], "total_hits": row["total_hits"]}

    def clear_expired_cache(self, days: int = 7) -> int:
        """清理超过N天的缓存条目。返回删除数量。"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM review_cache WHERE created_at < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount

    # ---- 审查历史(替代 ConversationMemory,落盘持久化) ----

    _MAX_REVIEW_HISTORY = 100

    def save_review_history(self, thread_id: str, prescription_text: str, result_summary: str = "") -> None:
        """记录一次审查到历史(落盘,保留最近 100 条)。"""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO review_history (thread_id, prescription_text, result_summary, created_at) "
            "VALUES (?, ?, ?, ?)",
            (thread_id, prescription_text, result_summary, datetime.now().isoformat()),
        )
        conn.execute(
            "DELETE FROM review_history WHERE id NOT IN "
            "(SELECT id FROM review_history ORDER BY id DESC LIMIT ?)",
            (self._MAX_REVIEW_HISTORY,),
        )
        conn.commit()

    def get_review_history(self, thread_id: str) -> Optional[dict]:
        """按 thread_id 查找最近一条审查历史。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT thread_id, prescription_text, result_summary, created_at "
            "FROM review_history WHERE thread_id = ? ORDER BY id DESC LIMIT 1",
            (thread_id,),
        ).fetchone()
        if not row:
            return None
        r = dict(row)
        return {
            "thread_id": r["thread_id"],
            "prescription_text": r["prescription_text"],
            "result_summary": r["result_summary"] or "",
            "timestamp": r["created_at"],
        }

    def list_review_history(self, n: int = 10) -> list[dict]:
        """获取最近 n 条审查历史。"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT thread_id, prescription_text, result_summary, created_at "
            "FROM review_history ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            out.append({
                "thread_id": d["thread_id"],
                "prescription_text": d["prescription_text"],
                "result_summary": d["result_summary"] or "",
                "timestamp": d["created_at"],
            })
        return out


db = Database()


def get_db() -> Database:
    """获取数据库单例。"""
    return db
