"""规则引擎优化器:从反馈中自动调整规则权重。

面试要点:
1. 规则不是写死的——系统会根据用户反馈自我优化
2. 误报(false positive)降低规则权重,漏报(false negative)提升权重
3. 权重衰减机制防止历史数据过度影响
4. 这是"闭环"的核心:反馈→分析→优化→更好

性能优化:
- 内存缓存:配置只在首次加载时读磁盘,后续读内存
- record_trigger 只更新缓存并标记 dirty,不立即写盘
- flush_config() 手动刷盘,或在进程退出时自动刷
"""
import atexit
import json
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "rules_config.json"

# ── 内存缓存 ──────────────────────────────────────────────
_cache: dict | None = None
_dirty: bool = False
_lock = threading.Lock()


def load_config() -> dict:
    """加载规则配置(优先读缓存,缓存未命中才读磁盘)。"""
    global _cache
    if _cache is not None:
        return _cache
    with _lock:
        # 双重检查:另一个线程可能已经加载了
        if _cache is not None:
            return _cache
        if not CONFIG_PATH.exists():
            logger.warning(f"规则配置文件不存在: {CONFIG_PATH}, 使用默认值")
            _cache = _default_config()
        else:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        return _cache


def save_config(config: dict) -> None:
    """保存规则配置(更新缓存 + 写磁盘)。"""
    global _cache, _dirty
    config["last_updated"] = datetime.now().isoformat()
    with _lock:
        _cache = config
        _dirty = False
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    logger.info("规则配置已保存")


def _reset_cache() -> None:
    """清空内存缓存(仅测试用)。"""
    global _cache, _dirty
    with _lock:
        _cache = None
        _dirty = False


def flush_config() -> None:
    """将脏缓存刷到磁盘(供 atexit 或手动调用)。"""
    global _dirty
    if not _dirty or _cache is None:
        return
    with _lock:
        if not _dirty:
            return
        _dirty = False
        config = _cache
    config["last_updated"] = datetime.now().isoformat()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    logger.info("规则配置已刷盘")


# 进程退出时自动刷盘
atexit.register(flush_config)


def get_rule_weight(rule_name: str) -> float:
    """获取规则权重,用于风险评分加权。"""
    config = load_config()
    rules = config.get("rules", {})
    rule = rules.get(rule_name, {})
    if not rule.get("enabled", True):
        return 0.0
    return rule.get("weight", 1.0)


def get_rule_severity(rule_name: str) -> str:
    """获取规则严重程度(可被动态调整)。"""
    config = load_config()
    rules = config.get("rules", {})
    rule = rules.get(rule_name, {})
    return rule.get("severity", "medium")


def record_trigger(rule_name: str) -> None:
    """记录规则触发次数(只更新缓存,不写磁盘)。"""
    global _dirty
    config = load_config()
    rules = config.get("rules", {})
    if rule_name in rules:
        rules[rule_name]["trigger_count"] = rules[rule_name].get("trigger_count", 0) + 1
        _dirty = True


def adjust_weight_from_feedback(
    rule_name: str,
    is_false_positive: bool = False,
    is_false_negative: bool = False,
) -> float:
    """根据反馈调整规则权重。

    Args:
        rule_name: 规则名称
        is_false_positive: 误报(规则触发但用户认为不需要)
        is_false_negative: 漏报(规则未触发但用户发现遗漏)

    Returns:
        调整后的权重
    """
    config = load_config()
    auto = config.get("auto_adjust", {})
    if not auto.get("enabled", True):
        return 1.0

    rules = config.get("rules", {})
    if rule_name not in rules:
        logger.warning(f"未知规则: {rule_name}")
        return 1.0

    rule = rules[rule_name]
    weight = rule.get("weight", 1.0)
    min_w = auto.get("min_weight", 0.3)
    max_w = auto.get("max_weight", 2.0)
    fp_penalty = auto.get("fp_penalty", 0.05)
    fn_boost = auto.get("fn_boost", 0.1)

    if is_false_positive:
        rule["false_positive_count"] = rule.get("false_positive_count", 0) + 1
        weight = max(min_w, weight - fp_penalty)
        rule["weight"] = weight
        logger.info(f"规则 {rule_name} 误报,权重降至 {weight:.2f}")

    if is_false_negative:
        rule["false_negative_count"] = rule.get("false_negative_count", 0) + 1
        weight = min(max_w, weight + fn_boost)
        rule["weight"] = weight
        logger.info(f"规则 {rule_name} 漏报,权重升至 {weight:.2f}")

    save_config(config)
    return weight


def analyze_feedback_and_adjust(feedback_records: list[dict]) -> dict:
    """批量分析反馈并调整规则权重。

    Args:
        feedback_records: 反馈记录列表,每条包含:
            - rule_name: 规则名
            - score: 1-5分
            - comment: 评论(可选)

    Returns:
        调整摘要
    """
    adjustments = {"fp_adjusted": 0, "fn_adjusted": 0, "skipped": 0}

    for record in feedback_records:
        rule_name = record.get("rule_name", "")
        score = record.get("score", 3)
        comment = record.get("comment", "")

        if not rule_name:
            adjustments["skipped"] += 1
            continue

        # 低分(1-2) + 有评论 → 可能是误报
        if score <= 2:
            adjust_weight_from_feedback(rule_name, is_false_positive=True)
            adjustments["fp_adjusted"] += 1
        # 高分(4-5) + 指出遗漏 → 可能是漏报
        elif score >= 4 and "漏" in comment:
            adjust_weight_from_feedback(rule_name, is_false_negative=True)
            adjustments["fn_adjusted"] += 1
        else:
            adjustments["skipped"] += 1

    return adjustments


def decay_weights(decay_rate: float = None) -> dict:
    """权重衰减:将所有权重向1.0回归,防止历史数据过度影响。

    每次调用将权重向1.0移动 decay_rate 的距离。
    """
    config = load_config()
    auto = config.get("auto_adjust", {})
    rate = decay_rate if decay_rate is not None else auto.get("decay_rate", 0.01)

    decayed = {}
    for rule_name, rule in config.get("rules", {}).items():
        old_weight = rule.get("weight", 1.0)
        if old_weight > 1.0:
            new_weight = max(1.0, old_weight - rate)
        elif old_weight < 1.0:
            new_weight = min(1.0, old_weight + rate)
        else:
            new_weight = 1.0
        rule["weight"] = round(new_weight, 4)
        if old_weight != new_weight:
            decayed[rule_name] = {"old": old_weight, "new": new_weight}

    save_config(config)
    return decayed


def get_rules_summary() -> dict:
    """获取规则引擎摘要,用于展示。"""
    config = load_config()
    rules = config.get("rules", {})

    total = len(rules)
    enabled = sum(1 for r in rules.values() if r.get("enabled", True))
    high_weight = sum(1 for r in rules.values() if r.get("weight", 1.0) > 1.2)
    low_weight = sum(1 for r in rules.values() if r.get("weight", 1.0) < 0.8)
    total_triggers = sum(r.get("trigger_count", 0) for r in rules.values())
    total_fp = sum(r.get("false_positive_count", 0) for r in rules.values())
    total_fn = sum(r.get("false_negative_count", 0) for r in rules.values())

    return {
        "total_rules": total,
        "enabled_rules": enabled,
        "high_weight_rules": high_weight,
        "low_weight_rules": low_weight,
        "total_triggers": total_triggers,
        "total_false_positives": total_fp,
        "total_false_negatives": total_fn,
        "version": config.get("version", "unknown"),
        "last_updated": config.get("last_updated"),
    }


def _default_config() -> dict:
    """默认配置(配置文件不存在时使用)。"""
    return {
        "version": "1.0.0",
        "rules": {},
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
