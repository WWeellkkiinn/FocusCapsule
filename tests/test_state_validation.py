import math

from focuscapsule.state import SessionConfig, validate_config


def test_validate_config_accepts_normal_and_disabled_interval_configs() -> None:
    assert validate_config(SessionConfig(25, 3, 5, 10, True)) == []
    assert validate_config(SessionConfig(25, 0, 0, 10, True)) == []
    assert validate_config(SessionConfig(25, 0.1, 0.2, 10, True)) == []


def test_validate_config_rejects_interval_configuration_errors() -> None:
    zero_min_errors = validate_config(SessionConfig(25, 0, 5, 10, True))
    negative_min_errors = validate_config(SessionConfig(25, -1, 5, 10, True))
    max_not_less_errors = validate_config(SessionConfig(5, 0.1, 5.0, 10, True))

    assert any("最小值为 0" in error for error in zero_min_errors)
    assert "随机区间最小值必须不少于 0 分钟" in negative_min_errors
    assert "随机区间最大值必须小于专注总时长" in max_not_less_errors


def test_validate_config_rejects_non_finite_interval_values() -> None:
    nan_errors = validate_config(SessionConfig(25, float("nan"), 5, 10, True))
    inf_errors = validate_config(SessionConfig(25, 1, math.inf, 10, True))

    assert any("随机区间最小值" in error and "有限数字" in error for error in nan_errors)
    assert any("随机区间最大值" in error and "有限数字" in error for error in inf_errors)


def test_validate_config_can_report_multiple_errors_together() -> None:
    errors = validate_config(SessionConfig(4, 6, 5, 200, True))

    assert len(errors) >= 3
