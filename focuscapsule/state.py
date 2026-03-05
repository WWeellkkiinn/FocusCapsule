from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SessionState(str, Enum):
    IDLE = "IDLE"
    FOCUSING = "FOCUSING"
    RESTING = "RESTING"
    FINISHED = "FINISHED"


@dataclass(slots=True)
class SessionConfig:
    total_minutes: int = 25
    interval_min_minutes: float = 3.0
    interval_max_minutes: float = 5.0
    break_seconds: int = 10
    sound_enabled: bool = True
    seed: int | None = None


@dataclass(slots=True)
class SessionRuntime:
    state: SessionState = SessionState.IDLE
    focus_total_sec: int = 0
    focus_remaining_sec: int = 0
    break_remaining_sec: int = 0
    trigger_points_sec: list[int] = field(default_factory=list)
    started_monotonic: float = 0.0
    paused_break_accumulated: float = 0.0
    rest_enter_monotonic: float | None = None
    active_trigger_points: set[int] = field(default_factory=set)


def validate_config(config: SessionConfig) -> list[str]:
    errors: list[str] = []
    if config.total_minutes < 5:
        errors.append("专注总时长必须不少于 5 分钟")
    if config.interval_min_minutes < 0:
        errors.append("随机区间最小值必须不少于 0 分钟")
    if config.interval_min_minutes > config.interval_max_minutes:
        errors.append("随机区间最小值不能大于最大值")
    if not (5 <= config.break_seconds <= 120):
        errors.append("休息时长必须在 5~120 秒之间")
    if config.interval_max_minutes * 60 >= config.total_minutes * 60:
        errors.append("随机区间最大值必须小于专注总时长")
    return errors
