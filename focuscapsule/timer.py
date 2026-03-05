from __future__ import annotations

import math
import time

from focuscapsule.state import SessionRuntime


class MonotonicFocusTimer:
    def __init__(self, runtime: SessionRuntime) -> None:
        self.runtime = runtime

    def start(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        self.runtime.started_monotonic = current
        self.runtime.paused_break_accumulated = 0.0
        self.runtime.rest_enter_monotonic = None

    def enter_rest(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        self.runtime.rest_enter_monotonic = current

    def exit_rest(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        if self.runtime.rest_enter_monotonic is None:
            return
        self.runtime.paused_break_accumulated += current - self.runtime.rest_enter_monotonic
        self.runtime.rest_enter_monotonic = None

    def compute_focus_remaining(self, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        elapsed = math.floor(current - self.runtime.started_monotonic) - int(
            self.runtime.paused_break_accumulated
        )
        remaining = max(0, self.runtime.focus_total_sec - elapsed)
        self.runtime.focus_remaining_sec = remaining
        return remaining

    def compute_break_remaining(self, break_total_sec: int, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        if self.runtime.rest_enter_monotonic is None:
            remaining = break_total_sec
        else:
            elapsed = math.floor(current - self.runtime.rest_enter_monotonic)
            remaining = max(0, break_total_sec - elapsed)
        self.runtime.break_remaining_sec = remaining
        return remaining
