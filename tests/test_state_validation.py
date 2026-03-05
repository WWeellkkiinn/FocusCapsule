from focuscapsule.state import SessionConfig, validate_config


def test_validate_config_ok() -> None:
    cfg = SessionConfig(25, 3, 5, 10, True)
    assert validate_config(cfg) == []


def test_validate_config_reject_invalid() -> None:
    cfg = SessionConfig(4, 6, 5, 200, True)
    errors = validate_config(cfg)
    assert len(errors) >= 3
