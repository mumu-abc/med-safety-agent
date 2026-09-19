"""端到端验证:真实跑一遍流水线,确认 reasoning_chain 真的有内容。

刻意选低风险处方(不触发 recommend 分支),把 LLM 调用压到最少。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("ENABLE_MEMORY", "false")

from app.routers.review import _build_raw_response  # noqa: E402
from app.workflow import review_prescription  # noqa: E402

state = review_prescription("患者男,45岁,无基础疾病。处方:对乙酰氨基酚 500mg tid 口服。")
resp = _build_raw_response(state)

chain = resp.get("reasoning_chain") or []
print(f"\n=== reasoning_chain: {len(chain)} 步 ===")
for s in chain:
    print(f"[{s['node']:<10}] {s['step']}")
    print(f"           {s['detail']}")

assert chain, "推理链为空!"
assert len(chain) == 6, f"应为 6 步,实际 {len(chain)}"
assert all(s["detail"].strip() for s in chain), "存在空的 detail"
print("\nOK: 推理链非空且字段完整")
