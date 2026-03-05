from __future__ import annotations

import customtkinter as ctk


class CapsuleWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("280x120+80+80")

        self.time_var = ctk.StringVar(value="00:00")
        frame = ctk.CTkFrame(self, corner_radius=18)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="专注剩余", font=("Microsoft YaHei", 14)).pack(pady=(10, 0))
        ctk.CTkLabel(frame, textvariable=self.time_var, font=("Consolas", 32)).pack(pady=(0, 4))

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=14, pady=(0, 12))

        self._drag_x = 0
        self._drag_y = 0
        frame.bind("<ButtonPress-1>", self._start_drag)
        frame.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event) -> None:
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    @staticmethod
    def _fmt(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def update_view(self, remaining_sec: int, total_sec: int) -> None:
        self.time_var.set(self._fmt(remaining_sec))
        ratio = 1.0 if total_sec == 0 else max(0.0, min(1.0, 1 - remaining_sec / total_sec))
        self.progress.set(ratio)
