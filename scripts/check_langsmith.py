"""LangSmith 可观测性自检脚本。

用途:确认 trace 是否真的上传到了 LangSmith,避免"配了半天其实一条都没记上"。

用法:
    python scripts/check_langsmith.py

检查流程:
    1. 确认 .env 里 LANGSMITH_TRACING=true 且 API_KEY 非空
    2. 真实调用一次 LLM(带 run_name,便于在平台上定位)
    3. 轮询 LangSmith 项目,确认这条 run 能被查到
    4. 检查项目里是否有「含子节点的树形 trace」(真正的 Agent 流水线)

第 4 步很有必要:曾经出现过"单次 LLM 调用追踪成功、但 LangGraph 流水线没有根 trace"
的情况——因为 tracing 开关是在「一次 run 开始时」读环境变量的,如果 `_setup_langsmith()`
只在 `get_llm()` 里懒调用,graph.invoke() 早就开始了,于是只留下一堆互不相连的 LLM run。
只看第 2 步会误判为"可观测性已配好",实际截不出一张能说明问题的流水线图。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

# LangSmith /runs/query 的 limit 硬上限(超过会返回 400 Bad Request)
_RUN_QUERY_LIMIT = 100


def main() -> int:
    tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    project = os.getenv("LANGSMITH_PROJECT", "med-safety-agent")

    print("=" * 56)
    print("LangSmith 自检")
    print("=" * 56)

    if not tracing:
        print("[FAIL] LANGSMITH_TRACING 不是 true,请先在 .env 里开启")
        return 1
    if not api_key:
        print("[FAIL] LANGSMITH_API_KEY 为空,请填入 LangSmith 的 API Key")
        return 1

    print(f"[OK] tracing 已开启,项目名: {project}")
    print(f"[OK] API Key 已配置 ({api_key[:8]}...{api_key[-4:]})")

    # 1) 触发一次真实调用
    print("\n[1/3] 发起一次带标记的 LLM 调用...")
    from app.llm import get_llm

    marker = f"selftest-{int(time.time())}"
    try:
        llm = get_llm()
        resp = llm.invoke(
            "只回复两个字:可用",
            config={"run_name": marker, "tags": ["selftest"]},
        )
        print(f"      LLM 返回: {resp.content[:30]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] LLM 调用失败: {e}")
        return 1

    # 2) 轮询确认 trace 已上传(平台侧有几秒延迟)
    print("\n[2/3] 等待 trace 上传并查询(最多 30 秒)...")
    from langsmith import Client

    client = Client()
    found = None
    for i in range(10):
        try:
            runs = list(
                client.list_runs(
                    project_name=project,
                    filter=f'eq(name, "{marker}")',
                    limit=1,
                )
            )
            if runs:
                found = runs[0]
                break
        except Exception as e:  # noqa: BLE001
            print(f"      第 {i + 1} 次查询出错: {type(e).__name__}: {e}")
        time.sleep(3)

    if found is None:
        print(
            "\n[WARN] 30 秒内没查到这条 trace。可能原因:\n"
            "  1) API Key 无效或属于别的组织\n"
            "  2) 网络到 api.smith.langchain.com 不通(可尝试代理)\n"
            "  3) 平台索引延迟,稍等后手动到网页端确认\n"
            f"  4) 项目名不一致(当前: {project})"
        )
        return 2

    print("\n[SUCCESS] 单次调用已捕获 trace!")
    print(f"      run name : {found.name}")
    print(f"      run id   : {found.id}")
    print(f"      status   : {found.status}")
    if found.end_time and found.start_time:
        print(f"      耗时     : {(found.end_time - found.start_time).total_seconds():.2f}s")

    # 3) 检查是否存在「树形」trace —— 只有它才能体现出 Agent 流水线结构
    # 注意:LangSmith /runs/query 的 limit 上限是 100,传更大会直接 400
    print("\n[3/3] 检查是否存在树形流水线 trace...")
    try:
        all_runs = list(client.list_runs(project_name=project, limit=_RUN_QUERY_LIMIT))
    except Exception as e:  # noqa: BLE001
        print(f"      [WARN] 列举 run 失败,跳过该检查: {type(e).__name__}: {e}")
        return 0

    kids: dict = {}
    for r in all_runs:
        kids.setdefault(r.parent_run_id, []).append(r)
    trees = [r for r in kids.get(None, []) if kids.get(r.id)]

    if trees:
        f = max(trees, key=lambda x: len(kids.get(x.id, [])))
        print(f"      [OK] 找到 {len(trees)} 条树形 trace,最大的一条:")
        print(f"           {f.name!r}  直接子节点 {len(kids.get(f.id, []))} 个")
        print(f"           子节点: {[k.name for k in kids.get(f.id, [])][:8]}")
        print(f"\n下一步:打开 https://smith.langchain.com → Projects → {project}")
        print(f"        点开这条 {f.name!r} 的 run,即可截到 parse→detect→rules→assess→report 瀑布图")
        return 0

    print(
        "      [WARN] 没找到含子节点的树形 trace。单次调用能记录,只说明 LLM 层通了;\n"
        "             流水线没成树,通常是因为 tracing 开关在 graph 开始执行之后才生效。\n"
        "             本项目已把 _setup_langsmith() 提到 app/llm.py 模块导入时执行,\n"
        "             若仍无树形 trace,请确认改动没被改回「只在 get_llm() 里调用」,\n"
        f"             然后跑一次完整审查:python -c \"from app.workflow import review_prescription; "
        f"review_prescription('华法林 5mg qd; 阿司匹林 100mg qd')\""
    )
    return 3


if __name__ == "__main__":
    sys.exit(main())
