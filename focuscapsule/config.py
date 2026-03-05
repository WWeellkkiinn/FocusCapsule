from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from focuscapsule.state import SessionConfig


CONFIG_PATH = Path.home() / ".focuscapsule" / "config.json"


def load_config() -> SessionConfig:
    if not CONFIG_PATH.exists():
        return SessionConfig()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return SessionConfig()

    defaults = SessionConfig()
    return SessionConfig(
        total_minutes=int(data.get("total_minutes", defaults.total_minutes)),
        interval_min_minutes=int(
            data.get("interval_min_minutes", defaults.interval_min_minutes)
        ),
        interval_max_minutes=int(
            data.get("interval_max_minutes", defaults.interval_max_minutes)
        ),
        break_seconds=int(data.get("break_seconds", defaults.break_seconds)),
        sound_enabled=bool(data.get("sound_enabled", defaults.sound_enabled)),
        seed=data.get("seed", defaults.seed),
    )


def save_config(config: SessionConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(config)
    CONFIG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
