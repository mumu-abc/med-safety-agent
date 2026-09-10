"""规则优化器测试。"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def temp_config(tmp_path):
    """创建临时配置文件,并重置缓存。"""
    from app.rules.rule_optimizer import _reset_cache
    config = {
        "version": "1.0.0",
        "last_updated": None,
        "rules": {
            "test_rule_a": {
                "enabled": True,
                "severity": "high",
                "weight": 1.0,
                "trigger_count": 0,
                "false_positive_count": 0,
                "false_negative_count": 0,
            },
            "test_rule_b": {
                "enabled": True,
                "severity": "critical",
                "weight": 1.5,
                "trigger_count": 5,
                "false_positive_count": 2,
                "false_negative_count": 0,
            },
            "test_rule_disabled": {
                "enabled": False,
                "severity": "medium",
                "weight": 0.5,
                "trigger_count": 0,
                "false_positive_count": 0,
                "false_negative_count": 0,
            },
        },
        "severity_weights": {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.3},
        "auto_adjust": {
            "enabled": True,
            "min_weight": 0.3,
            "max_weight": 2.0,
            "fp_penalty": 0.05,
            "fn_boost": 0.1,
            "decay_rate": 0.01,
        },
    }
    config_file = tmp_path / "rules_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    # 重置缓存,确保每个测试从干净状态开始
    _reset_cache()
    yield config_file
    _reset_cache()


def test_load_config(temp_config):
    """加载配置文件。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import load_config
        config = load_config()
        assert config["version"] == "1.0.0"
        assert "test_rule_a" in config["rules"]


def test_get_rule_weight(temp_config):
    """获取规则权重。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import get_rule_weight
        assert get_rule_weight("test_rule_a") == 1.0
        assert get_rule_weight("test_rule_b") == 1.5


def test_get_rule_weight_disabled(temp_config):
    """禁用规则权重为0。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import get_rule_weight
        assert get_rule_weight("test_rule_disabled") == 0.0


def test_get_rule_weight_unknown(temp_config):
    """未知规则权重为1.0。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import get_rule_weight
        assert get_rule_weight("nonexistent_rule") == 1.0


def test_get_rule_severity(temp_config):
    """获取规则严重程度。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import get_rule_severity
        assert get_rule_severity("test_rule_a") == "high"
        assert get_rule_severity("test_rule_b") == "critical"


def test_adjust_weight_false_positive(temp_config):
    """误报降权。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import adjust_weight_from_feedback
        new_w = adjust_weight_from_feedback("test_rule_a", is_false_positive=True)
        assert new_w == 0.95  # 1.0 - 0.05


def test_adjust_weight_false_negative(temp_config):
    """漏报升权。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import adjust_weight_from_feedback
        new_w = adjust_weight_from_feedback("test_rule_a", is_false_negative=True)
        assert new_w == 1.1  # 1.0 + 0.1


def test_adjust_weight_min_bound(temp_config):
    """权重不低于最小值。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import adjust_weight_from_feedback
        # 多次误报降到最低
        for _ in range(100):
            adjust_weight_from_feedback("test_rule_a", is_false_positive=True)
        w = adjust_weight_from_feedback("test_rule_a", is_false_positive=True)
        assert w >= 0.3  # min_weight


def test_adjust_weight_max_bound(temp_config):
    """权重不超过最大值。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import adjust_weight_from_feedback
        for _ in range(100):
            adjust_weight_from_feedback("test_rule_a", is_false_negative=True)
        w = adjust_weight_from_feedback("test_rule_a", is_false_negative=True)
        assert w <= 2.0  # max_weight


def test_record_trigger(temp_config):
    """记录触发次数。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import record_trigger, load_config
        record_trigger("test_rule_a")
        config = load_config()
        assert config["rules"]["test_rule_a"]["trigger_count"] == 1


def test_analyze_feedback_batch(temp_config):
    """批量分析反馈。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import analyze_feedback_and_adjust
        feedback = [
            {"rule_name": "test_rule_a", "score": 1, "comment": "误报"},
            {"rule_name": "test_rule_b", "score": 4, "comment": "漏检了"},
            {"rule_name": "", "score": 3, "comment": ""},
        ]
        result = analyze_feedback_and_adjust(feedback)
        assert result["fp_adjusted"] == 1
        assert result["fn_adjusted"] == 1
        assert result["skipped"] == 1


def test_decay_weights(temp_config):
    """权重衰减。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import decay_weights, load_config
        decayed = decay_weights(decay_rate=0.1)
        config = load_config()
        # test_rule_b 权重 1.5 → 1.4
        assert config["rules"]["test_rule_b"]["weight"] == 1.4
        # test_rule_disabled 权重 0.5 → 0.6
        assert config["rules"]["test_rule_disabled"]["weight"] == 0.6


def test_get_rules_summary(temp_config):
    """规则摘要。"""
    with patch("app.rules.rule_optimizer.CONFIG_PATH", temp_config):
        from app.rules.rule_optimizer import get_rules_summary
        summary = get_rules_summary()
        assert summary["total_rules"] == 3
        assert summary["enabled_rules"] == 2
        assert summary["total_triggers"] == 5


def test_calculate_risk_score():
    """加权风险评分。"""
    from app.rules.safety_rules import calculate_risk_score
    risks = [
        {"severity": "critical", "weight": 1.0},
        {"severity": "high", "weight": 0.8},
    ]
    score = calculate_risk_score(risks)
    assert score > 0
    assert score <= 100


def test_calculate_risk_score_empty():
    """空风险评分为0。"""
    from app.rules.safety_rules import calculate_risk_score
    assert calculate_risk_score([]) == 0.0
