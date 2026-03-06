from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

# Smallest interval that rounds to at least 1 second: 1/60 minutes ≈ 0.0167 minutes
_MIN_INTERVAL_MINUTES = 1 / 60


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
    start_mode: str = "main"


@dataclass(slots=True)
class SessionRuntime:
    state: SessionState = SessionState.IDLE
    focus_total_sec: int = 0
    focus_remaining_sec: int = 0
    break_remaining_sec: int = 0
    trigger_points_sec: list[int] = field(default_factory=list)
    started_monotonic: float = 0.0
    rest_enter_monotonic: float | None = None
    active_trigger_points: set[int] = field(default_factory=set)


def validate_config(config: SessionConfig) -> list[str]:
    errors: list[str] = []

    # Reject NaN / Infinity before any arithmetic or comparison
    for val, label in [
        (config.interval_min_minutes, "随机区间最小值"),
        (config.interval_max_minutes, "随机区间最大值"),
    ]:
        if not math.isfinite(val):
            errors.append(f"{label}必须是有限数字")
    if errors:
        return errors

    if config.total_minutes < 5:
        errors.append("专注总时长必须不少于 5 分钟")

    # Interval semantics:
    #   - Both 0 → micro-breaks disabled (valid)
    #   - Otherwise → min must be > 0, both must convert to ≥ 1 second, and min ≤ max
    if config.interval_min_minutes == 0.0 and config.interval_max_minutes == 0.0:
        pass  # micro-breaks explicitly disabled
    elif config.interval_min_minutes < 0:
        errors.append("随机区间最小值必须不少于 0 分钟")
    elif config.interval_min_minutes == 0.0:
        errors.append("随机区间最小值为 0 时最大值也须为 0（关闭微休息），否则请设置大于 0 的最小值")
    elif config.interval_min_minutes > config.interval_max_minutes:
        errors.append("随机区间最小值不能大于最大值")
    else:
        min_sec = math.ceil(config.interval_min_minutes * 60)
        max_sec = math.floor(config.interval_max_minutes * 60)
        if min_sec < 1:
            errors.append(
                f"随机区间最小值换算后不足 1 秒，请输入不小于 {_MIN_INTERVAL_MINUTES:.3f} 分钟的值"
            )
        if max_sec < 1:
            errors.append(
                f"随机区间最大值换算后不足 1 秒，请输入不小于 {_MIN_INTERVAL_MINUTES:.3f} 分钟的值"
            )

    if not (5 <= config.break_seconds <= 120):
        errors.append("休息时长必须在 5~120 秒之间")
    if config.interval_max_minutes * 60 >= config.total_minutes * 60:
        errors.append("随机区间最大值必须小于专注总时长")
    return errors
