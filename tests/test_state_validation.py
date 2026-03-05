from focuscapsule.state import SessionConfig, validate_config


def test_validate_config_ok() -> None:
    cfg = SessionConfig(25, 3, 5, 10, True)
    assert validate_config(cfg) == []


def test_validate_config_allow_zero_interval_min() -> None:
    cfg = SessionConfig(25, 0, 5, 10, True)
    assert validate_config(cfg) == []


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
