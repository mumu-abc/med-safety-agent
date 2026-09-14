"""CI 用的知识图谱数据完整性校验。

单独成文件是为了让 CI 和本地跑的是同一段逻辑(避免把断言塞进 YAML 里变成字符串地狱)。

注意「交互条数」有两个口径,别混用:
    - 原始条目 439:INTERACTIONS 列表的长度,含 A-B / B-A 反向重复
    - 去重后 396 :按无序对去重后的真实药对数量(README 里报的是这个)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.drug_data import DRUGS, INTERACTIONS, validate_data  # noqa: E402


def main() -> None:
    report = validate_data(strict=True)  # 有悬挂引用会直接抛
    uniq_pairs = {frozenset((a, b)) for a, b, _s, _m in INTERACTIONS}
    self_loops = [(a, b) for a, b, _s, _m in INTERACTIONS if a == b]

    print(f"药物      : {len({d['id'] for d in DRUGS})}")
    print(f"交互      : 原始 {len(INTERACTIONS)} 条 → 去重后 {len(uniq_pairs)} 对")
    print(f"自环      : {len(self_loops)}")
    print(f"悬挂引用  : {report['dangling_count']}")

    assert report["dangling_count"] == 0, f"存在悬挂引用: {report['dangling']}"
    assert not self_loops, f"存在自环: {self_loops}"
    print("OK")


if __name__ == "__main__":
    main()
