import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_eval import run_evaluation

r = run_evaluation(run_full=True, save_report=True)
print(json.dumps(r, ensure_ascii=False, default=str)[:1500])
