from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from focuscapsule.audio import play_alert
from focuscapsule.config import load_config, save_config
from focuscapsule.scheduler import build_trigger_points
from focuscapsule.state import SessionConfig, SessionRuntime, SessionState, validate_config
from focuscapsule.timer import MonotonicFocusTimer
from focuscapsule.ui.capsule_window import CapsuleWindow
from focuscapsule.ui.main_window import MainSettingsWindow
from focuscapsule.ui.overlay_window import OverlayWindow


class FocusCapsuleApp:
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = load_config()
        self.runtime = SessionRuntime()
        self.timer = MonotonicFocusTimer(self.runtime)

        self.main_window = MainSettingsWindow(self.start_session)
        self.main_window.set_form(self.config)
        self.main_window.protocol("WM_DELETE_WINDOW", self._shutdown)

        self.capsule: CapsuleWindow | None = None
        self.overlay = OverlayWindow(self.main_window, self.skip_rest)
        self.tick_job = None

    def run(self) -> None:
        self.main_window.mainloop()

    def start_session(self, config: SessionConfig) -> None:
        errors = validate_config(config)
        if errors:
            self.main_window.show_error("；".join(errors))
            return

        self.config = config
        save_config(config)

        total_sec = config.total_minutes * 60
        trigger_points = build_trigger_points(
            total_sec=total_sec,
            min_interval_sec=config.interval_min_minutes * 60,
            max_interval_sec=config.interval_max_minutes * 60,
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

        self.main_window.withdraw()
        if self.capsule is None or not self.capsule.winfo_exists():
            self.capsule = CapsuleWindow(self.main_window)
        self.capsule.deiconify()
        self.capsule.update_view(total_sec, total_sec)

        self._schedule_tick()

    def _schedule_tick(self) -> None:
        if self.tick_job is not None:
            self.main_window.after_cancel(self.tick_job)
        self.tick_job = self.main_window.after(200, self._tick)

    def _tick(self) -> None:
        if self.runtime.state == SessionState.FOCUSING:
            remaining = self.timer.compute_focus_remaining()
            if self.capsule and self.capsule.winfo_exists():
                self.capsule.update_view(remaining, self.runtime.focus_total_sec)

            if remaining in self.runtime.active_trigger_points:
                self.runtime.active_trigger_points.remove(remaining)
                self.enter_rest()
                return

            if remaining <= 0:
                self.finish_session()
                return

        elif self.runtime.state == SessionState.RESTING:
            self.runtime.break_remaining_sec -= 1
            self.overlay.update_countdown(self.runtime.break_remaining_sec)
            if self.runtime.break_remaining_sec <= 0:
                self.exit_rest("timeout")

        self._schedule_tick()

    def enter_rest(self) -> None:
        self.runtime.state = SessionState.RESTING
        self.runtime.break_remaining_sec = self.config.break_seconds
        self.timer.enter_rest()
        self.overlay.show(self.runtime.break_remaining_sec)
        play_alert(self.config.sound_enabled)
        self._schedule_tick()

    def exit_rest(self, _reason: str) -> None:
        self.overlay.hide()
        self.timer.exit_rest()
        self.runtime.state = SessionState.FOCUSING
        self._schedule_tick()

    def skip_rest(self) -> None:
        if self.runtime.state == SessionState.RESTING:
            self.exit_rest("esc")

    def finish_session(self) -> None:
        self.runtime.state = SessionState.FINISHED
        if self.tick_job is not None:
            self.main_window.after_cancel(self.tick_job)
            self.tick_job = None
        self.overlay.hide()
        if self.capsule and self.capsule.winfo_exists():
            self.capsule.withdraw()
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()
        messagebox.showinfo("FocusCapsule", "本次专注已完成。")

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
