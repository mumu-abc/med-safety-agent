"""清理「结构已过期」的审查缓存。

背景:
    响应结构一旦新增字段(例如 reasoning_chain),旧缓存里存的还是老结构的 JSON。
    命中旧缓存时新字段自然缺失 —— 前端「推理链」tab 就会白屏,而且用户很难理解
    为什么"同一条处方,别人有内容我没有"。

策略:
    只删「result_json 里缺少当前必需字段」的条目,不动其他缓存。
    默认预览,加 --apply 真删。

用法:
    python scripts/clear_stale_cache.py                # 预览
    python scripts/clear_stale_cache.py --apply        # 删除
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 当前响应必须具备的字段;缺任何一个都说明这条缓存是旧结构
REQUIRED_FIELDS = ("reasoning_chain",)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--field", default=None, help="只检查某个字段(默认检查 REQUIRED_FIELDS 全部)")
    args = ap.parse_args()

    from app.database import get_db

    fields = (args.field,) if args.field else REQUIRED_FIELDS

    db = get_db()
    conn = db._get_conn()
    rows = conn.execute(
        "SELECT id, prescription_text, result_json FROM review_cache"
    ).fetchall() if _has_id(conn) else conn.execute(
        "SELECT rowid AS id, prescription_text, result_json FROM review_cache"
    ).fetchall()
    conn2 = conn
    print("=" * 64)
    print(f"审查缓存体检   共 {len(rows)} 条   检查字段: {', '.join(fields)}")
    print("=" * 64)

    stale, ok = [], 0
    for r in rows:
        try:
            data = json.loads(r["result_json"])
        except Exception:
            stale.append((r["id"], r["prescription_text"], "JSON 解析失败"))
            continue
        missing = [f for f in fields if f not in data]
        if missing:
            stale.append((r["id"], r["prescription_text"], f"缺 {','.join(missing)}"))
        else:
            ok += 1

    for _id, text, why in stale:
        print(f"  [旧结构] {(text or '')[:44]:<46} {why}")
    print("-" * 64)
    print(f"结构正常 {ok} 条;待清理 {len(stale)} 条")

    if not args.apply:
        print("\n这是预览。加 --apply 真正删除。")
        return 0

    for _id, _t, _w in stale:
        conn2.execute("DELETE FROM review_cache WHERE rowid = ?", (_id,))
    conn2.commit()
    left = conn2.execute("SELECT COUNT(*) AS c FROM review_cache").fetchone()["c"]
    print(f"\n[完成] 已删除 {len(stale)} 条;缓存剩余 {left} 条")
    return 0


def _has_id(conn) -> bool:
    cols = [c[1] for c in conn.execute("PRAGMA table_info(review_cache)").fetchall()]
    return "id" in cols


if __name__ == "__main__":
    sys.exit(main())
