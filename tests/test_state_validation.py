import math

from focuscapsule.state import SessionConfig, validate_config


def test_validate_config_ok() -> None:
    cfg = SessionConfig(25, 3, 5, 10, True)
    assert validate_config(cfg) == []


def test_validate_config_disabled_intervals() -> None:
    """Both 0 means micro-breaks disabled — should be valid."""
    cfg = SessionConfig(25, 0, 0, 10, True)
    assert validate_config(cfg) == []


def test_validate_config_reject_zero_min_nonzero_max() -> None:
    """min=0 with max>0 is ambiguous — silently produces no breaks, so reject."""
    cfg = SessionConfig(25, 0, 5, 10, True)
    errors = validate_config(cfg)
    assert any("最小值为 0" in e for e in errors)


def test_validate_config_allow_decimal_intervals() -> None:
    cfg = SessionConfig(25, 0.1, 0.2, 10, True)
    assert validate_config(cfg) == []


def test_validate_config_reject_negative_interval_min() -> None:
    cfg = SessionConfig(25, -1, 5, 10, True)
    errors = validate_config(cfg)
    assert "随机区间最小值必须不少于 0 分钟" in errors


def test_validate_config_reject_interval_max_not_less_than_total() -> None:
    cfg = SessionConfig(5, 0.1, 5.0, 10, True)
    errors = validate_config(cfg)
    assert "随机区间最大值必须小于专注总时长" in errors


def test_validate_config_reject_invalid() -> None:
    cfg = SessionConfig(4, 6, 5, 200, True)
    errors = validate_config(cfg)
    assert len(errors) >= 3


def test_validate_config_reject_nan_interval_min() -> None:
    cfg = SessionConfig(25, float("nan"), 5, 10, True)
    errors = validate_config(cfg)
    assert any("随机区间最小值" in e and "有限数字" in e for e in errors)


def test_validate_config_reject_inf_interval_max() -> None:
    cfg = SessionConfig(25, 1, math.inf, 10, True)
    errors = validate_config(cfg)
    assert any("随机区间最大值" in e and "有限数字" in e for e in errors)
