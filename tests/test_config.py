from pathlib import Path

from focuscapsule.config import load_config, save_config
from focuscapsule.state import SessionConfig


def test_save_and_load_config_persists_capsule_position(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)

    save_config(SessionConfig(capsule_x=-1440, capsule_y=160))
    loaded = load_config()

    assert loaded.capsule_x == -1440
    assert loaded.capsule_y == 160
    assert loaded.finish_break_minutes == 5


def test_load_config_uses_none_when_capsule_position_missing(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('{"total_minutes": 25}', encoding="utf-8")

    loaded = load_config()

    assert loaded.capsule_x is None
    assert loaded.capsule_y is None
    assert loaded.finish_break_minutes == 5


def test_load_config_ignores_invalid_capsule_position_without_dropping_other_fields(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '{"total_minutes": 30, "break_seconds": 15, "capsule_x": "", "capsule_y": "abc"}',
        encoding="utf-8",
    )

    loaded = load_config()

    assert loaded.total_minutes == 30
    assert loaded.break_seconds == 15
    assert loaded.capsule_x is None
    assert loaded.capsule_y is None


def test_save_and_load_config_persists_finish_break_minutes(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)

    save_config(SessionConfig(finish_break_minutes=8))
    loaded = load_config()

    assert loaded.finish_break_minutes == 8


def test_load_config_defaults_finish_break_minutes_when_missing(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('{"total_minutes": 30, "break_seconds": 15}', encoding="utf-8")

    loaded = load_config()

    assert loaded.total_minutes == 30
    assert loaded.break_seconds == 15
    assert loaded.finish_break_minutes == 5


def test_load_config_ignores_invalid_finish_break_minutes_without_dropping_other_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr("focuscapsule.config.CONFIG_PATH", config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '{"total_minutes": 30, "break_seconds": 15, "finish_break_minutes": "abc", "capsule_x": 80, "capsule_y": 120}',
        encoding="utf-8",
    )

    loaded = load_config()

    assert loaded.total_minutes == 30
    assert loaded.break_seconds == 15
    assert loaded.finish_break_minutes == 5
    assert loaded.capsule_x == 80
    assert loaded.capsule_y == 120
