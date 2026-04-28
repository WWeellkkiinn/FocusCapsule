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
        self.runtime.rest_enter_monotonic = None

    def enter_rest(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        self.runtime.rest_enter_monotonic = current

    def exit_rest(self, _now: float | None = None) -> None:
        if self.runtime.rest_enter_monotonic is None:
            return
        self.runtime.rest_enter_monotonic = None

    def compute_focus_remaining(self, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        elapsed = math.floor(current - self.runtime.started_monotonic)
        remaining = max(0, self.runtime.focus_total_sec - elapsed)
        self.runtime.focus_remaining_sec = remaining
        return remaining

    def pause(self, now: float | None = None) -> None:
        self.runtime.pause_enter_monotonic = time.monotonic() if now is None else now

    def resume(self, now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        elapsed = current - self.runtime.pause_enter_monotonic
        self.runtime.started_monotonic += elapsed
        if self.runtime.rest_enter_monotonic is not None:
            self.runtime.rest_enter_monotonic += elapsed

    def compute_break_remaining(self, break_total_sec: int, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        if self.runtime.rest_enter_monotonic is None:
            remaining_f = float(break_total_sec)
            remaining = break_total_sec
        else:
            elapsed = current - self.runtime.rest_enter_monotonic
            remaining_f = max(0.0, break_total_sec - elapsed)
            remaining = max(0, break_total_sec - math.floor(elapsed))
        self.runtime.break_remaining_float = remaining_f
        self.runtime.break_remaining_sec = remaining
        return remaining
