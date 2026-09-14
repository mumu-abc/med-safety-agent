"""LLM 配额自检（只读，1 秒出结果）

用途：跑评测 / 演示前先确认 API 可用，避免跑一小时全是降级输出。

用法：
    python scripts/check_quota.py

退出码：
    0 = 配额正常
    2 = 不可用（429 / 网络 / key 错误），此时不要跑评测
"""

import os
import sys
import time
from pathlib import Path

# 允许直接 python scripts/check_quota.py 运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or ""

    if not api_key:
        print("[X] 未配置 LLM_API_KEY，请检查 .env")
        return 2

    print("=" * 60)
    print(f"模型    : {model or '(未配置)'}")
    print(f"endpoint: {base_url or '(默认)'}")
    print(f"key     : {api_key[:8]}...{api_key[-4:]} (长度 {len(api_key)})")
    print("正在发送一次极小请求…")

    try:
        from openai import OpenAI
    except ImportError:
        print("[X] 未安装 openai：pip install openai")
        return 2

    client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=60, max_retries=1)
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "只输出一个数字：1+1等于几"}],
            max_tokens=300,
            temperature=0,
        )
    except Exception as e:
        msg = str(e)
        print("-" * 60)
        print(f"[X] 配额不可用：{msg[:300]}")
        print()
        if "429" in msg or "quota" in msg.lower() or "insufficient" in msg.lower():
            print("原因：额度已用尽（429）。评测会静默走降级路径，")
            print("      产出无效样本，请不要开跑。")
        else:
            print("原因：网络 / key / 模型名问题，请核对 .env。")
        print("=" * 60)
        return 2

    msg = resp.choices[0].message
    content = (msg.content or "").strip()
    elapsed = time.time() - t0
    usage = getattr(resp, "usage", None)
    total = getattr(usage, "total_tokens", 0) if usage else 0

    print("-" * 60)
    print(f"[OK] 配额正常，耗时 {elapsed:.1f}s，消耗 {total} tokens")
    print(f"     模型回复：{content[:80]!r}")
    print()
    print("可以跑评测了：")
    print("  python scripts/eval_external_holdout.py    # 外部 holdout 集")
    print("  python scripts/eval_llm_increment.py       # LLM 增量难例集")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
