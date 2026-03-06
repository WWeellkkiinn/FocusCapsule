from __future__ import annotations

import customtkinter as ctk
import sys
import tkinter as tk


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


class CapsuleWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, on_finish_focus=None, on_show_main=None) -> None:
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._transparent_key = "#00FF00"
        self.configure(fg_color=self._transparent_key)
        self._enable_transparent_background()
        self.geometry("280x120+80+80")
        self._position_initialized = False
        self._on_finish_focus = on_finish_focus
        self._on_show_main = on_show_main

        self.time_var = ctk.StringVar(value="00:00")
        frame = ctk.CTkFrame(self, corner_radius=18, fg_color="#FFFFFF", border_width=1, border_color="#D7DEE8")
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="专注剩余",
            font=("Microsoft YaHei", 14),
            text_color="#243447",
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            frame,
            textvariable=self.time_var,
            font=("Consolas", 32),
            text_color="#0F172A",
        ).pack(pady=(0, 4))

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.configure(
            fg_color="#E5EAF2",
            progress_color="#3B82F6",
            border_color="#C9D4E3",
            border_width=1,
        )
        self.progress.set(0)
        self.progress.pack(fill="x", padx=14, pady=(0, 12))

        self._drag_x = 0
        self._drag_y = 0
        frame.bind("<ButtonPress-1>", self._start_drag)
        frame.bind("<B1-Motion>", self._on_drag)
        frame.bind("<Button-3>", self._show_context_menu)

        self._menu = tk.Menu(self, tearoff=0)
        self._menu.add_command(label="结束专注", command=self._finish_focus)
        self._menu.add_command(label="显示主界面", command=self._show_main)

    def _start_drag(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event) -> None:
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")
        self._position_initialized = True

    def _show_context_menu(self, event) -> str:
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()
        return "break"

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

    def set_default_position(self, margin: int = 24) -> None:
        if self._position_initialized:
            return
        self.update_idletasks()
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

    @staticmethod
    def _fmt(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def update_view(self, remaining_sec: int, total_sec: int) -> None:
        self.time_var.set(self._fmt(remaining_sec))
        ratio = 1.0 if total_sec == 0 else max(0.0, min(1.0, 1 - remaining_sec / total_sec))
        self.progress.set(ratio)
