from __future__ import annotations

import customtkinter as ctk
import sys
import tkinter as tk

DEFAULT_CAPSULE_WIDTH = 188
DEFAULT_CAPSULE_HEIGHT = 72
ACTIVE_TIME_FONT = ("Consolas", 24)
FINISHED_TIME_FONT = ("Microsoft YaHei", 13, "bold")
FINISHED_TEXT = "专注结束，点击重启"


def compute_bottom_right_position(
    screen_width: int,
    screen_height: int,
    window_width: int,
    window_height: int,
    margin: int = 24,
) -> tuple[int, int]:
    x = max(margin, int(screen_width) - int(window_width) - margin)
    y = max(margin, int(screen_height) - int(window_height) - margin)
    return x, y


def compute_drag_position(
    window_x: int,
    window_y: int,
    current_root_x: int,
    current_root_y: int,
    previous_root_x: int,
    previous_root_y: int,
) -> tuple[int, int]:
    return (
        window_x + current_root_x - previous_root_x,
        window_y + current_root_y - previous_root_y,
    )


class CapsuleWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk,
        on_finish_focus=None,
        on_show_main=None,
        on_restart_focus=None,
        on_position_change=None,
    ) -> None:
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._transparent_key = "#00FF00"
        self.configure(fg_color=self._transparent_key)
        self._enable_transparent_background()
        self.geometry(f"{DEFAULT_CAPSULE_WIDTH}x{DEFAULT_CAPSULE_HEIGHT}+80+80")
        self._position_initialized = False
        self._on_finish_focus = on_finish_focus
        self._on_show_main = on_show_main
        self._on_restart_focus = on_restart_focus
        self._on_position_change = on_position_change

        self.time_var = ctk.StringVar(value="00:00")
        self._drag_root_x = 0
        self._drag_root_y = 0
        self._drag_moved = False
        self._restart_enabled = False
        self._pending_click_job = None

        frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#FFFFFF", border_width=1, border_color="#D7DEE8")
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        self.time_label = ctk.CTkLabel(
            frame,
            textvariable=self.time_var,
            font=ACTIVE_TIME_FONT,
            text_color="#0F172A",
            justify="center",
            wraplength=148,
        )
        self.time_label.grid(row=1, column=0, pady=(0, 6), padx=14)

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.configure(
            fg_color="#E5EAF2",
            progress_color="#3B82F6",
            border_color="#C9D4E3",
            border_width=1,
            height=8,
        )
        self.progress.set(0)
        self.progress.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 0))

        self._bind_pointer_events(frame)

    def _bind_pointer_events(self, widget) -> None:
        widget.bind("<ButtonPress-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._on_drag)
        widget.bind("<ButtonRelease-1>", self._on_left_release)
        widget.bind("<Double-Button-1>", self._on_double_click)
        widget.bind("<Control-Button-1>", self._on_ctrl_click)
        for child in widget.winfo_children():
            self._bind_pointer_events(child)

    def _start_drag(self, event) -> None:
        self._cancel_pending_click()
        self._drag_root_x = event.x_root
        self._drag_root_y = event.y_root
        self._drag_moved = False

    def _on_drag(self, event) -> None:
        x, y = compute_drag_position(
            window_x=self.winfo_x(),
            window_y=self.winfo_y(),
            current_root_x=event.x_root,
            current_root_y=event.y_root,
            previous_root_x=self._drag_root_x,
            previous_root_y=self._drag_root_y,
        )
        self.geometry(f"+{x}+{y}")
        self._drag_root_x = event.x_root
        self._drag_root_y = event.y_root
        self._drag_moved = True
        self._position_initialized = True
        if callable(self._on_position_change):
            self._on_position_change(x, y)

    def _on_left_release(self, _event) -> str | None:
        if self._drag_moved or not self._restart_enabled:
            return None
        self._cancel_pending_click()
        self._pending_click_job = self.after(220, self._restart_focus)
        return "break"

    def _on_double_click(self, _event) -> str:
        self._cancel_pending_click()
        self._show_main()
        return "break"

    def _on_ctrl_click(self, _event) -> str:
        self._cancel_pending_click()
        self._finish_focus()
        return "break"

    def _cancel_pending_click(self) -> None:
        if self._pending_click_job is None:
            return
        try:
            self.after_cancel(self._pending_click_job)
        except Exception:
            pass
        self._pending_click_job = None

    def _enable_transparent_background(self) -> None:
        if sys.platform != "win32":
            self.configure(fg_color="#FFFFFF")
            return
        try:
            self.wm_attributes("-transparentcolor", self._transparent_key)
        except tk.TclError:
            self.configure(fg_color="#FFFFFF")

    def _finish_focus(self) -> None:
        if callable(self._on_finish_focus):
            self._on_finish_focus()

    def _show_main(self) -> None:
        if callable(self._on_show_main):
            self._on_show_main()

    def _restart_focus(self) -> None:
        self._pending_click_job = None
        if callable(self._on_restart_focus):
            self._on_restart_focus()

    def set_default_position(
        self,
        margin: int = 24,
        preferred_position: tuple[int, int] | None = None,
    ) -> None:
        if self._position_initialized:
            return
        self.update_idletasks()
        if preferred_position is not None:
            x, y = preferred_position
        else:
            width = self.winfo_width()
            height = self.winfo_height()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x, y = compute_bottom_right_position(
                screen_width=screen_width,
                screen_height=screen_height,
                window_width=width,
                window_height=height,
                margin=margin,
            )
        self.geometry(f"+{x}+{y}")
        self._position_initialized = True

    def get_position(self) -> tuple[int, int]:
        return self.winfo_x(), self.winfo_y()

    @staticmethod
    def _fmt(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def update_view(self, remaining_sec: int, total_sec: int) -> None:
        self._cancel_pending_click()
        self._restart_enabled = False
        self.time_var.set(self._fmt(remaining_sec))
        self.time_label.configure(font=ACTIVE_TIME_FONT)
        ratio = 1.0 if total_sec == 0 else max(0.0, min(1.0, 1 - remaining_sec / total_sec))
        self.progress.set(ratio)

    def show_finished_state(self) -> None:
        self._cancel_pending_click()
        self._restart_enabled = True
        self.time_var.set(FINISHED_TEXT)
        self.time_label.configure(font=FINISHED_TIME_FONT)
        self.progress.set(1.0)
