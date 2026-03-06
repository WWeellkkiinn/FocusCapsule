from __future__ import annotations

import dataclasses
import math
import customtkinter as ctk

from focuscapsule.audio import play_double_alert, play_triple_alert
from focuscapsule.config import load_config, save_config
from focuscapsule.scheduler import build_trigger_points
from focuscapsule.state import SessionConfig, SessionRuntime, SessionState, validate_config
from focuscapsule.timer import MonotonicFocusTimer
from focuscapsule.ui.capsule_window import (
    DEFAULT_CAPSULE_HEIGHT,
    DEFAULT_CAPSULE_WIDTH,
    CapsuleWindow,
    compute_clamped_capsule_position,
    compute_default_capsule_position,
    get_display_bounds,
)
from focuscapsule.ui.main_window import MainSettingsWindow, normalize_start_mode
from focuscapsule.ui.overlay_window import OverlayWindow


class FocusCapsuleApp:
    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.config = load_config()
        self.runtime = SessionRuntime()
        self.timer = MonotonicFocusTimer(self.runtime)
        self.current_mode = normalize_start_mode(self.config.start_mode)

        self.main_window = MainSettingsWindow(
            self.start_session,
            on_switch_to_capsule=self.switch_to_capsule_mode,
            on_end_session=self.end_session_early,
        )
        self.main_window.set_form(self.config)
        self.main_window.protocol("WM_DELETE_WINDOW", self._shutdown)
        self._normalize_capsule_position_on_launch()

        self.capsule: CapsuleWindow | None = None
        self.overlay = OverlayWindow(self.main_window, self.skip_rest)
        self.tick_job = None
        self._last_finish_message = "本次专注已完成。"

    def run(self) -> None:
        self.main_window.mainloop()

    def start_session(self, config: SessionConfig) -> None:
        config = dataclasses.replace(
            config,
            seed=None,
            capsule_x=self.config.capsule_x,
            capsule_y=self.config.capsule_y,
        )
        errors = validate_config(config)
        if errors:
            self.main_window.show_error("；".join(errors))
            return

        self.config = config
        self.current_mode = normalize_start_mode(config.start_mode)
        self._try_save_config(config)

        total_sec = config.total_minutes * 60
        min_interval_sec = max(0, math.ceil(config.interval_min_minutes * 60))
        max_interval_sec = max(0, math.floor(config.interval_max_minutes * 60))
        # Ensure that rounding does not produce an inverted interval range
        max_interval_sec = max(max_interval_sec, min_interval_sec)
        trigger_points = build_trigger_points(
            total_sec=total_sec,
            min_interval_sec=min_interval_sec,
            max_interval_sec=max_interval_sec,
            guard_tail_sec=max(45, config.break_seconds * 2),
            seed=config.seed,
        )

        self.runtime = SessionRuntime(
            state=SessionState.FOCUSING,
            focus_total_sec=total_sec,
            focus_remaining_sec=total_sec,
            break_remaining_sec=config.break_seconds,
            trigger_points_sec=trigger_points,
            active_trigger_points=set(trigger_points),
        )
        self.timer = MonotonicFocusTimer(self.runtime)
        self.timer.start()

        self._ensure_capsule()
        self._apply_display_mode()
        if self.current_mode == "main":
            self._refresh_main_session_view(self.runtime.focus_remaining_sec)
        self._schedule_tick()

    def _ensure_capsule(self) -> CapsuleWindow:
        if self.capsule is None or not self.capsule.winfo_exists():
            self.capsule = CapsuleWindow(
                self.main_window,
                on_finish_focus=self.end_session_early,
                on_show_main=self.show_main_window,
                on_restart_focus=self.restart_finished_session,
                on_position_change=self.remember_capsule_position,
            )
            self.capsule.withdraw()
        return self.capsule

    def _is_capsule_visible(self) -> bool:
        return bool(
            self.capsule
            and self.capsule.winfo_exists()
            and self.capsule.state() != "withdrawn"
        )

    def _hide_capsule(self) -> None:
        if self.capsule and self.capsule.winfo_exists():
            self.capsule.withdraw()

    def _show_capsule(self) -> None:
        capsule = self._ensure_capsule()
        capsule.deiconify()
        capsule.attributes("-topmost", True)
        capsule.set_default_position(preferred_position=self._validated_capsule_position())
        capsule.update_view(
            self.runtime.focus_remaining_sec,
            self.runtime.focus_total_sec,
        )

    def _show_main_mode(self) -> None:
        self.current_mode = "main"
        self._hide_capsule()
        self.main_window.show_session_view()
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()

    def _show_capsule_mode(self) -> None:
        self.current_mode = "capsule"
        self.main_window.withdraw()
        self._show_capsule()

    def _apply_display_mode(self) -> None:
        if self.current_mode == "capsule":
            self._show_capsule_mode()
        else:
            self._show_main_mode()

    def _schedule_tick(self) -> None:
        if self.tick_job is not None:
            self.main_window.after_cancel(self.tick_job)
        self.tick_job = self.main_window.after(200, self._tick)

    def _tick(self) -> None:
        if self.runtime.state == SessionState.FOCUSING:
            remaining = self.timer.compute_focus_remaining()
            self.runtime.focus_remaining_sec = remaining
            self._refresh_focus_views(remaining)

            if remaining in self.runtime.active_trigger_points:
                self.runtime.active_trigger_points.remove(remaining)
                self.enter_rest()
                return

            if remaining <= 0:
                self.finish_session()
                return

        elif self.runtime.state == SessionState.RESTING:
            focus_remaining = self.timer.compute_focus_remaining()
            self.runtime.focus_remaining_sec = focus_remaining
            if self.current_mode == "main":
                self._refresh_main_session_view(
                    focus_remaining,
                    status_text=f"微休息中，还剩 {self.timer.compute_break_remaining(self.config.break_seconds)} 秒恢复专注。",
                    switch_enabled=False,
                )
            if focus_remaining <= 0:
                self.finish_session()
                return

            remaining = self.timer.compute_break_remaining(self.config.break_seconds)
            self.overlay.update_countdown(remaining)
            if remaining <= 0:
                self.exit_rest("timeout")
                return

        self._schedule_tick()

    def _refresh_focus_views(self, remaining_sec: int) -> None:
        if self.current_mode == "main":
            self._refresh_main_session_view(remaining_sec)
        elif self._is_capsule_visible():
            self.capsule.update_view(remaining_sec, self.runtime.focus_total_sec)

    def _refresh_main_session_view(
        self,
        remaining_sec: int,
        status_text: str = "当前正在专注，请保持节奏。",
        switch_enabled: bool = True,
    ) -> None:
        self.main_window.update_session_view(
            remaining_sec=remaining_sec,
            total_sec=self.runtime.focus_total_sec,
            status_text=status_text,
            switch_enabled=switch_enabled,
        )

    def switch_to_capsule_mode(self) -> None:
        if self.runtime.state != SessionState.FOCUSING:
            if self.current_mode == "main":
                self._refresh_main_session_view(
                    self.runtime.focus_remaining_sec,
                    status_text="微休息中，暂时不能切换显示模式。",
                    switch_enabled=False,
                )
            return

        if self.current_mode == "main":
            self._show_capsule_mode()

    def enter_rest(self) -> None:
        self.runtime.state = SessionState.RESTING
        self.runtime.break_remaining_sec = self.config.break_seconds
        self.timer.enter_rest()
        self._hide_capsule()
        if self.current_mode == "main":
            self._refresh_main_session_view(
                self.runtime.focus_remaining_sec,
                status_text=f"微休息中，还剩 {self.config.break_seconds} 秒恢复专注。",
                switch_enabled=False,
            )
        self.overlay.show(self.runtime.break_remaining_sec)
        play_double_alert(self.config.sound_enabled)
        self._schedule_tick()

    def exit_rest(self, _reason: str) -> None:
        self.overlay.hide()
        self.timer.exit_rest()
        self.runtime.state = SessionState.FOCUSING
        self._apply_display_mode()
        play_double_alert(self.config.sound_enabled)
        if self.current_mode == "main":
            self._refresh_main_session_view(
                self.runtime.focus_remaining_sec,
                status_text="休息结束，继续专注。",
                switch_enabled=True,
            )
        self._schedule_tick()

    def skip_rest(self) -> None:
        if self.runtime.state == SessionState.RESTING:
            self.exit_rest("esc")

    def end_session_early(self) -> None:
        self._close_session("已提前结束本次专注。")

    def finish_session(self) -> None:
        self._last_finish_message = "本次专注已完成。"
        if self.current_mode == "capsule" and self._is_capsule_visible():
            self.runtime.state = SessionState.FINISHED
            if self.tick_job is not None:
                self.main_window.after_cancel(self.tick_job)
                self.tick_job = None
            self.overlay.hide()
            self.main_window.show_config_view(status_message=self._last_finish_message)
            self.capsule.show_finished_state()
            play_triple_alert(self.config.sound_enabled)
            return
        self._close_session(self._last_finish_message)

    def _close_session(self, message: str) -> None:
        self._last_finish_message = message
        self.runtime.state = SessionState.FINISHED
        if self.tick_job is not None:
            self.main_window.after_cancel(self.tick_job)
            self.tick_job = None
        self.overlay.hide()
        self._hide_capsule()
        self.current_mode = normalize_start_mode(self.config.start_mode)
        self.main_window.show_config_view(status_message=message)
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()
        play_triple_alert(self.config.sound_enabled)

    def show_main_window(self) -> None:
        if self.runtime.state == SessionState.FINISHED:
            self.current_mode = "main"
            self._hide_capsule()
            self.main_window.show_config_view(status_message=self._last_finish_message)
            self.main_window.deiconify()
            self.main_window.lift()
            self.main_window.focus_force()
            return
        self._show_main_mode()
        self._refresh_main_session_view(self.runtime.focus_remaining_sec)

    def restart_finished_session(self) -> None:
        if self.runtime.state != SessionState.FINISHED:
            return
        restart_config = dataclasses.replace(self.config, start_mode="capsule")
        self.start_session(restart_config)

    def remember_capsule_position(self, x: int, y: int) -> None:
        if self.config.capsule_x == int(x) and self.config.capsule_y == int(y):
            return
        self.config = dataclasses.replace(self.config, capsule_x=int(x), capsule_y=int(y))
        self._try_save_config(self.config)

    def _saved_capsule_position(self) -> tuple[int, int] | None:
        if self.config.capsule_x is None or self.config.capsule_y is None:
            return None
        return self.config.capsule_x, self.config.capsule_y

    def _display_bounds(self) -> list[tuple[int, int, int, int]]:
        return get_display_bounds(
            self.main_window.winfo_screenwidth(),
            self.main_window.winfo_screenheight(),
        )

    def _default_capsule_position(self) -> tuple[int, int]:
        return compute_default_capsule_position(
            screen_width=self.main_window.winfo_screenwidth(),
            screen_height=self.main_window.winfo_screenheight(),
            window_width=DEFAULT_CAPSULE_WIDTH,
            window_height=DEFAULT_CAPSULE_HEIGHT,
            display_bounds=self._display_bounds(),
        )

    def _validated_capsule_position(self) -> tuple[int, int]:
        saved_position = self._saved_capsule_position()
        if saved_position is None:
            return self._default_capsule_position()
        return compute_clamped_capsule_position(
            x=saved_position[0],
            y=saved_position[1],
            window_width=DEFAULT_CAPSULE_WIDTH,
            window_height=DEFAULT_CAPSULE_HEIGHT,
            display_bounds=self._display_bounds(),
        )

    def _normalize_capsule_position_on_launch(self) -> None:
        normalized = self._validated_capsule_position()
        if self.config.capsule_x == normalized[0] and self.config.capsule_y == normalized[1]:
            return
        self.config = dataclasses.replace(
            self.config,
            capsule_x=normalized[0],
            capsule_y=normalized[1],
        )
        self._try_save_config(self.config)

    @staticmethod
    def _try_save_config(config: SessionConfig) -> None:
        try:
            save_config(config)
        except OSError:
            return

    def _shutdown(self) -> None:
        if self.tick_job is not None:
            self.main_window.after_cancel(self.tick_job)
            self.tick_job = None
        self.overlay.hide()
        if self.capsule and self.capsule.winfo_exists():
            self.capsule.destroy()
        self.main_window.destroy()


def launch_app() -> None:
    FocusCapsuleApp().run()
