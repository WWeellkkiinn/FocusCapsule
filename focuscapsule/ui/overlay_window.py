from __future__ import annotations

import customtkinter as ctk


class OverlayWindow:
    def __init__(self, master: ctk.CTk, on_skip) -> None:
        self.master = master
        self.on_skip = on_skip
        self.windows: list[ctk.CTkToplevel] = []
        self.countdown_var = ctk.StringVar(value="10")

    def show(self, seconds: int) -> None:
        self.hide()
        self.countdown_var.set(str(seconds))
        screen_specs = self._screen_specs()

        for width, height, x, y in screen_specs:
            win = ctk.CTkToplevel(self.master)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                win.attributes("-alpha", 0.88)
            except Exception:
                pass
            win.geometry(f"{width}x{height}+{x}+{y}")
            win.configure(fg_color="#111111")
            win.bind("<Escape>", lambda _e: self.on_skip())

            frame = ctk.CTkFrame(win, fg_color="transparent")
            frame.place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(
                frame,
                text="微休息时间：请转动脖子、闭眼深呼吸",
                font=("Microsoft YaHei", 30, "bold"),
            ).pack(pady=(0, 16))
            ctk.CTkLabel(frame, textvariable=self.countdown_var, font=("Consolas", 72)).pack()
            ctk.CTkLabel(
                frame,
                text="按 Esc 键可跳过本次休息",
                font=("Microsoft YaHei", 16),
            ).pack(pady=(16, 0))

            win.focus_force()
            self.windows.append(win)

    def update_countdown(self, seconds: int) -> None:
        self.countdown_var.set(str(max(0, seconds)))

    def hide(self) -> None:
        for win in self.windows:
            try:
                win.destroy()
            except Exception:
                pass
        self.windows.clear()

    def _screen_specs(self) -> list[tuple[int, int, int, int]]:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            monitors: list[tuple[int, int, int, int]] = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_long * 4),
                ctypes.c_double,
            )

            def callback(_monitor, _hdc, rect_ptr, _data):
                rect = rect_ptr.contents
                left, top, right, bottom = rect[0], rect[1], rect[2], rect[3]
                monitors.append((right - left, bottom - top, left, top))
                return 1

            user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(callback), 0)
            if monitors:
                return monitors
        except Exception:
            pass

        return [(
            self.master.winfo_screenwidth(),
            self.master.winfo_screenheight(),
            0,
            0,
        )]
