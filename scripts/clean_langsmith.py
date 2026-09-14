"""清理 LangSmith 项目里的「垃圾 run」。

背景:
    pytest 在没有隔离 tracing 的早期版本下跑过,把大量只有 0 token 的
    构造型输入(如 {"raw_text": "处方A: 华法林"})当作真实 run 传了上去;
    scripts/check_langsmith.py 的自检调用(selftest-*)也都留在项目里。
    这些 run 和真正的流水线 trace 混在一起,截图时非常干扰。

策略:
    按 trace_id 分组。真正的 Agent 流水线是一条「有子节点的树」,
    垃圾 run 全是互不相连的孤立节点。默认保留「token 最多的那条树形 trace」,
    其余整条 trace 一起删除。

用法:
    python scripts/clean_langsmith.py                 # 只预览,不删除
    python scripts/clean_langsmith.py --apply         # 真正删除
    python scripts/clean_langsmith.py --apply --keep <trace_id>

实现说明(踩过的坑):
    1. langsmith 0.11.0 的 client.list_runs(offset=...) 的 offset 参数是被忽略的,
       传 offset 会永远返回同一页 —— 用它翻页会死循环。所以这里不走 SDK,直接打 HTTP API。
    2. POST /runs/query 的 `session` 字段必须是「列表」,传字符串会 422。
    3. 分页靠响应里的 cursors.next,不是 offset。单次 limit 最大 100,
       不翻页会漏掉大半 run(真实流水线一次审查有 200+ 个 run)。
    4. 删除没有 DELETE /runs/{id}(405),要用 POST /runs/delete 并给 trace_ids。

⚠️ 重要结论(2026-09-15 实测):
    在当前账号档位下,**run 级删除是不生效的** —— POST /runs/delete 会返回
    202 `{"message":"Run deletes queued"}`,看着成功了,但隔多久查 run 都还在。
    真正能用的是**项目级删除**:DELETE /sessions/{project_id} 返回 202 且确实生效
    (用临时项目验证过:name 再查返回空数组)。
    所以本脚本只能当「体检/预览」用;真要清干净,正确姿势是:
        1. 用新的 LANGSMITH_PROJECT 名跑一次真实审查,生成一个只含 1 条 trace 的项目
        2. 确认 trace 是完整树形之后,DELETE 掉旧项目
        3. PATCH /sessions/{新项目id} {"name": 旧名字} 把项目改回正式名称(实测可用)
    这套流程的每一步都已验证通过。
"""

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://api.smith.langchain.com"
_PAGE = 100
_MAX_PAGES = 50  # 安全阀,防止分页逻辑出问题时无限拉取


def _headers() -> dict:
    return {
        "x-api-key": os.getenv("LANGSMITH_API_KEY", "").strip(),
        "Content-Type": "application/json",
    }


def get_session_id(cl: httpx.Client, project: str) -> str | None:
    r = cl.get(f"{_BASE}/sessions", headers=_headers(), params={"name": project})
    r.raise_for_status()
    data = r.json()
    return data[0]["id"] if data else None


def fetch_all_runs(cl: httpx.Client, session_id: str) -> list[dict]:
    """游标翻页取回项目下全部 run。"""
    runs, cursor, pages = [], None, 0
    while pages < _MAX_PAGES:
        body = {"session": [session_id], "limit": _PAGE}
        if cursor:
            body["cursor"] = cursor
        r = cl.post(f"{_BASE}/runs/query", headers=_headers(), json=body)
        r.raise_for_status()
        page = r.json()
        runs.extend(page.get("runs", []))
        cursor = (page.get("cursors") or {}).get("next")
        pages += 1
        if not cursor:
            break
    return runs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正执行删除(默认只预览)")
    ap.add_argument("--keep", default=None, help="显式指定要保留的 trace_id")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="激进模式:只保留 token 最多的那条树形 trace(默认会额外保留所有有 token 的 trace)",
    )
    args = ap.parse_args()

    project = os.getenv("LANGSMITH_PROJECT", "med-safety-agent")
    if not os.getenv("LANGSMITH_API_KEY", "").strip():
        print("[FAIL] LANGSMITH_API_KEY 为空")
        return 1

    print("=" * 64)
    print(f"LangSmith 清理   project={project}")
    print("=" * 64)

    with httpx.Client(timeout=30) as cl:
        session_id = get_session_id(cl, project)
        if not session_id:
            print(f"[FAIL] 找不到项目 {project!r}")
            return 1
        print(f"项目 id: {session_id}")

        runs = fetch_all_runs(cl, session_id)
        print(f"共取回 {len(runs)} 条 run\n")
        if not runs:
            return 0

        # 按 trace 分组
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in runs:
            groups[r["trace_id"]].append(r)

        # 哪些 trace 是「树」(组内有父子关系)
        tree_traces = []
        for tid, members in groups.items():
            ids = {m["id"] for m in members}
            if any(m.get("parent_run_id") in ids for m in members):
                tree_traces.append(tid)

        # 决定保留谁
        if args.keep:
            keep = {args.keep}
        elif tree_traces:
            keep = {
                max(
                    tree_traces,
                    key=lambda t: sum(
                        ((m.get("total_tokens") or 0) for m in groups[t])
                    ),
                )
            }
        else:
            print("[FAIL] 没找到任何树形 trace,不敢盲删。请用 --keep 指定要保留的 trace")
            return 2

        # 非激进模式下,额外保留所有「有真实 token 消耗」的 trace ——
        # 它们可能是真实的审查调用,只是没长成完整树,不能当垃圾删掉。
        if not args.strict:
            keep |= {
                tid
                for tid, members in groups.items()
                if sum((m.get("total_tokens") or 0) for m in members) > 0
            }

        # selftest-* 是 scripts/check_langsmith.py 自检时造的探针 run,
        # 无论有没有 token 都算垃圾,一律不保留。
        keep = {
            tid
            for tid in keep
            if not all(
                str(m.get("name") or "").startswith("selftest-") for m in groups[tid]
            )
        }

        hdr = f"{'状态':<6}{'trace_id':<38}{'run数':>5}{'tokens':>9}  名称"
        print(hdr)
        print("-" * 100)
        to_delete: list[str] = []
        for tid, members in sorted(
            groups.items(),
            key=lambda kv: -sum((m.get("total_tokens") or 0) for m in kv[1]),
        ):
            tokens = sum((m.get("total_tokens") or 0) for m in members)
            names = sorted({(m.get("name") or "?") for m in members})
            mark = "保留" if tid in keep else "删除"
            if tid not in keep:
                to_delete.append(tid)
            star = "  [树]" if tid in tree_traces else ""
            print(
                f"{mark:<6}{str(tid):<38}{len(members):>5}{tokens:>9}  "
                f"{','.join(names)[:34]}{star}"
            )

        print("-" * 100)
        n_keep = sum(len(groups[t]) for t in keep if t in groups)
        print(f"保留 {len(keep)} 条 trace / {n_keep} 个 run;待删除 {len(to_delete)} 条 trace")

        if not args.apply:
            print("\n这是预览。确认无误后加 --apply 真正删除。")
            return 0

        print("\n开始删除...")
        ok = fail = 0
        for i in range(0, len(to_delete), 50):
            batch = to_delete[i : i + 50]
            r = cl.post(
                f"{_BASE}/runs/delete",
                headers=_headers(),
                json={"session_id": session_id, "trace_ids": batch},
            )
            if r.status_code < 300:
                ok += len(batch)
            else:
                fail += len(batch)
                print(f"  [WARN] 批次失败 {r.status_code}: {r.text[:160]}")
        print(f"[完成] 删除 trace {ok} 条,失败 {fail} 条")

        left = fetch_all_runs(cl, session_id)
        total_tokens = sum((m.get("total_tokens") or 0) for m in left)
        print(f"复查:项目里现在还剩 {len(left)} 条 run,合计 {total_tokens} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
