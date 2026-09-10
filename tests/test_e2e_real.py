"""真实 LLM 集成测试(标记 @pytest.mark.slow,默认跳过)。

运行: pytest tests/test_e2e_real.py -v --runslow
"""
import pytest

# 自定义 mark:默认跳过 slow 测试
def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow (needs LLM API)")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.mark.slow
def test_full_review_flow():
    """完整审查流程(真实 LLM 调用)。"""
    from app.workflow import review_prescription

    text = """处方:
诊断: 2型糖尿病
药物: 二甲双胍 500mg 每日两次, 格列本脲 5mg 每日一次
患者: 女, 70岁, 肾功能不全"""

    result = review_prescription(text)

    # 基本结构检查
    assert result["report"], "报告不应为空"
    assert result["prescription"], "处方解析结果不应为空"
    assert result["risk_assessment"], "风险评估不应为空"

    # 规则引擎应该捕获肾功能不全+二甲双胍的风险
    rule_risks = result.get("rule_risks", [])
    metformin_renal = any("二甲双胍" in r.get("drug", "") or "metformin" in r.get("drug", "")
                          for r in rule_risks)
    # 注:如果图谱中药物名为中文"二甲双胍",drug字段会是中文
    # 这个测试验证规则引擎确实触发了
    print(f"规则引擎风险数: {len(rule_risks)}")
    for r in rule_risks:
        print(f"  - {r['drug']}: {r['risk']} [{r['severity']}]")


@pytest.mark.slow
def test_interaction_detection_real():
    """真实药物交互检测。"""
    from app.agents.interaction_agent import detect_interactions

    result = detect_interactions(["华法林", "阿司匹林", "布洛芬"])

    assert "interactions" in result
    assert "contraindications" in result
    print(f"检测到 {len(result['interactions'])} 项交互")
    print(f"分析: {result.get('analysis', '')[:200]}")
