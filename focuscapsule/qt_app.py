"""Qt-based FocusCapsule application — replaces app.py UI layer."""
from __future__ import annotations

import dataclasses
import math
import os
import sys
import time

# Must be set before QApplication is created
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from focuscapsule.config import load_config, save_config
from focuscapsule.scheduler import build_trigger_points
from focuscapsule.state import (
    SessionConfig,
    SessionRuntime,
    SessionState,
    validate_config,
)
from focuscapsule.timer import MonotonicFocusTimer
from focuscapsule.virtual_desktop import VirtualDesktopController
from focuscapsule.ui.bar_bridge import BarBridge
from focuscapsule.ui.bar_window import BarWindow

_VD_SYNC_INTERVAL = 1.0


class FocusCapsuleQtApp:
    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setQuitOnLastWindowClosed(False)

        self.config = load_config()
        self.runtime = SessionRuntime()
        self._timer = MonotonicFocusTimer(self.runtime)
        self._vd = VirtualDesktopController()
        self._last_vd_sync = 0.0
        self.bridge = BarBridge(self)
        self.window = BarWindow(self.bridge, saved_x=self.config.capsule_x)

        self._tick_timer = QTimer()
        self._tick_timer.setInterval(250)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    def run(self) -> None:
        self._push_snapshot()
        sys.exit(self.qapp.exec())

    # ── Tick loop ─────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._sync_virtual_desktop()
        state = self.runtime.state

        if state == SessionState.PAUSED:
            return

        if state == SessionState.FOCUSING:
            remaining = self._timer.compute_focus_remaining()
            self.runtime.focus_remaining_sec = remaining

            triggered = {p for p in self.runtime.active_trigger_points if remaining <= p}
            if triggered:
                self.runtime.active_trigger_points -= triggered
                self._enter_micro_rest()
                return

            if remaining <= 0:
                self._enter_finish_rest()
                return

        elif state == SessionState.MICRO_RESTING:
            focus_rem = self._timer.compute_focus_remaining()
            self.runtime.focus_remaining_sec = focus_rem

            if focus_rem <= 0:
                self._enter_finish_rest()
                return

            break_rem = self._timer.compute_break_remaining(self.config.break_seconds)
            self.runtime.break_remaining_sec = break_rem
            if break_rem <= 0:
                self._exit_micro_rest()
                return

        elif state == SessionState.FINISH_RESTING:
            remaining = self._timer.compute_break_remaining(self._finish_break_sec())
            self.runtime.break_remaining_sec = remaining
            if remaining <= 0:
                self._complete_finish_rest()
                return

        self._push_snapshot()

    # ── State transitions ─────────────────────────────────────────────────────

    def _enter_micro_rest(self) -> None:
        self.runtime.state = SessionState.MICRO_RESTING
        self.runtime.break_remaining_sec = self.config.break_seconds
        self._timer.enter_rest()
        self._push_snapshot()

    def _exit_micro_rest(self) -> None:
        self._timer.exit_rest()
        self.runtime.state = SessionState.FOCUSING
        self._push_snapshot()

    def _enter_finish_rest(self) -> None:
        self.runtime.state = SessionState.FINISH_RESTING
        self.runtime.focus_remaining_sec = 0
        self.runtime.break_remaining_sec = self._finish_break_sec()
        self._timer.enter_rest()
        self._push_snapshot()

    def _complete_finish_rest(self) -> None:
        if self.config.auto_next:
            self._apply_session_start(self.config)
            return
        self.runtime.state = SessionState.FINISHED
        self.runtime.break_remaining_sec = 0
        self._push_snapshot()

    def _finish_break_sec(self) -> int:
        return self.config.finish_break_minutes * 60

    # ── Virtual desktop sync ──────────────────────────────────────────────────

    def _sync_virtual_desktop(self) -> None:
        now = time.monotonic()
        if now - self._last_vd_sync < _VD_SYNC_INTERVAL:
            return
        self._last_vd_sync = now
        try:
            hwnd = self.window.own_hwnd()
            if hwnd:
                self._vd.sync_window(hwnd)
        except Exception:
            pass

    # ── Bridge-facing API ─────────────────────────────────────────────────────

    def start_session_with_draft(self, draft: dict) -> list[str]:
        try:
            cfg = self._parse_draft(draft)
        except (TypeError, ValueError, KeyError) as exc:
            return [f"参数格式错误：{exc}"]

        errors = validate_config(cfg)
        if errors:
            return errors

        self.config = dataclasses.replace(
            self.config,
            total_minutes=cfg.total_minutes,
            interval_min_minutes=cfg.interval_min_minutes,
            interval_max_minutes=cfg.interval_max_minutes,
            break_seconds=cfg.break_seconds,
            finish_break_minutes=cfg.finish_break_minutes,
        )
        self._try_save_config(self.config)
        self._apply_session_start(self.config)
        return []

    def _apply_session_start(self, cfg: SessionConfig) -> None:
        total_sec = cfg.total_minutes * 60
        min_sec = max(0, math.ceil(cfg.interval_min_minutes * 60))
        max_sec = max(min_sec, math.floor(cfg.interval_max_minutes * 60))
        trigger_points = build_trigger_points(
            total_sec=total_sec,
            min_interval_sec=min_sec,
            max_interval_sec=max_sec,
            guard_tail_sec=max(45, cfg.break_seconds * 2),
            seed=None,
        )
        self.runtime = SessionRuntime(
            state=SessionState.FOCUSING,
            focus_total_sec=total_sec,
            focus_remaining_sec=total_sec,
            break_remaining_sec=cfg.break_seconds,
            trigger_points_sec=trigger_points,
            active_trigger_points=set(trigger_points),
        )
        self._timer = MonotonicFocusTimer(self.runtime)
        self._timer.start()
        self._push_snapshot()

    def toggle_auto_next(self) -> None:
        self.config = dataclasses.replace(self.config, auto_next=not self.config.auto_next)
        self._try_save_config(self.config)
        self._push_snapshot()

    def pause_session(self) -> None:
        state = self.runtime.state
        if state == SessionState.PAUSED:
            self._timer.resume()
            self.runtime.state = SessionState(self.runtime.paused_from)
        elif state in (SessionState.FOCUSING, SessionState.MICRO_RESTING, SessionState.FINISH_RESTING):
            self.runtime.paused_from = state.value
            self.runtime.state = SessionState.PAUSED
            self._timer.pause()
        self._push_snapshot()

    def end_session(self) -> None:
        if self.runtime.state in (SessionState.MICRO_RESTING, SessionState.FINISH_RESTING):
            self._timer.exit_rest()
        self.runtime.state = SessionState.FINISHED
        self.runtime.focus_remaining_sec = 0
        self.runtime.break_remaining_sec = 0
        self._push_snapshot()

    def quit(self) -> None:
        self._tick_timer.stop()
        self._vd.close()
        self.qapp.quit()

    def remember_bar_x(self, x: int) -> None:
        if self.config.capsule_x == x:
            return
        self.config = dataclasses.replace(self.config, capsule_x=x)
        self._try_save_config(self.config)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _push_snapshot(self) -> None:
        self.bridge.push_snapshot(self.runtime, self.config)

    @staticmethod
    def _parse_draft(draft: dict) -> SessionConfig:
        return SessionConfig(
            total_minutes=int(draft["total_minutes"]),
            interval_min_minutes=float(draft["interval_min_minutes"]),
            interval_max_minutes=float(draft["interval_max_minutes"]),
            break_seconds=int(draft["break_seconds"]),
            finish_break_minutes=int(draft["finish_break_minutes"]),
        )

    @staticmethod
    def _try_save_config(config: SessionConfig) -> None:
        try:
            save_config(config)
        except OSError:
            pass


def launch_qt_app() -> None:
    FocusCapsuleQtApp().run()
