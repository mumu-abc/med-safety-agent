import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.drug_data import ALTERNATIVES

print("原始条目:", len(ALTERNATIVES))
print("去重后无序对:", len({frozenset((a, b)) for a, b, _r in ALTERNATIVES}))
