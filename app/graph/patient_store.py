"""患者档案存储(内存 + JSON持久化)。

P2-20修复:加 threading.Lock 保证并发安全,
写入用原子操作(先写临时文件再 rename)。
"""
import json
import os
import tempfile
import threading
from pathlib import Path
from app.config import settings

_patients: dict[str, dict] = {}
_loaded: bool = False
_lock = threading.Lock()
_store_path = Path(settings.graph_path).parent / "patients.json"


def _load():
    global _patients, _loaded
    if _store_path.exists():
        with open(_store_path, encoding="utf-8") as f:
            _patients = json.load(f)
    _loaded = True


def _save():
    """原子写入:先写临时文件,再 rename,避免写到一半崩溃导致数据损坏。"""
    _store_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=_store_path.parent, suffix=".tmp", prefix="patients_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(_patients, f, ensure_ascii=False, indent=2)
        Path(tmp_path).replace(_store_path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _ensure_loaded():
    """确保数据已加载（用 _loaded 标记而非 _patients 是否为空）。"""
    global _loaded
    if not _loaded:
        _load()


def get_patient(patient_id: str) -> dict | None:
    with _lock:
        _ensure_loaded()
        return _patients.get(patient_id)


def save_patient(patient_id: str, data: dict) -> None:
    with _lock:
        _ensure_loaded()
        _patients[patient_id] = data
        _save()


def list_patients() -> list[dict]:
    with _lock:
        _ensure_loaded()
        return [{"id": pid, **data} for pid, data in _patients.items()]
