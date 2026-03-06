from __future__ import annotations

import customtkinter as ctk

OVERLAY_BG_COLOR = "#050816"
OVERLAY_TITLE_COLOR = "#F8FAFC"
OVERLAY_COUNTDOWN_COLOR = "#FFFFFF"
OVERLAY_HINT_COLOR = "#DCE7F5"


def _build_geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{int(width)}x{int(height)}{int(x):+d}{int(y):+d}"


def _scale_overlay_size(size: int, pixels_per_inch: float) -> int:
    if pixels_per_inch <= 0:
        return int(size)
    return max(1, int(round(int(size) * 96.0 / float(pixels_per_inch))))


class OverlayWindow:
    def __init__(self, master: ctk.CTk, on_skip) -> None:
        self.master = master
        self.on_skip = on_skip
        self.windows: list[ctk.CTkToplevel] = []
        self.countdown_var = ctk.StringVar(value="10")
        self._master_escape_bind_id: str | None = None
        self._activation_job = None

    def show(self, seconds: int) -> None:
        self.hide()
        self.countdown_var.set(str(seconds))
        screen_specs = self._screen_specs()
        pixels_per_inch = float(self.master.winfo_fpixels("1i"))

        for width, height, x, y in screen_specs:
            win = ctk.CTkToplevel(self.master)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                win.attributes("-alpha", 0.94)
            except Exception:
                pass
            logical_width = _scale_overlay_size(width, pixels_per_inch)
            logical_height = _scale_overlay_size(height, pixels_per_inch)
            win.geometry(_build_geometry(logical_width, logical_height, x, y))
            win.configure(fg_color=OVERLAY_BG_COLOR)
            win.bind("<Escape>", self._handle_escape)
            center_layer = ctk.CTkFrame(win, fg_color="transparent")
            center_layer.pack(fill="both", expand=True)
            center_layer.grid_rowconfigure(0, weight=1)
            center_layer.grid_columnconfigure(0, weight=1)

            frame = ctk.CTkFrame(center_layer, fg_color="transparent")

            ctk.CTkLabel(
                frame,
                text="微休息时间：请转动脖子、闭眼深呼吸",
                font=("Microsoft YaHei", 30, "bold"),
                text_color=OVERLAY_TITLE_COLOR,
            ).pack(pady=(0, 16))
            ctk.CTkLabel(
                frame,
                textvariable=self.countdown_var,
                font=("Consolas", 72),
                text_color=OVERLAY_COUNTDOWN_COLOR,
            ).pack()
            ctk.CTkLabel(
                frame,
                text="按 Esc 键可跳过本次休息",
                font=("Microsoft YaHei", 16),
                text_color=OVERLAY_HINT_COLOR,
            ).pack(pady=(16, 0))
            frame.grid(row=0, column=0)

            self.windows.append(win)

        self._bind_master_escape()
        self._activate_windows()
        self._activation_job = self.master.after(80, self._activate_windows)

    def update_countdown(self, seconds: int) -> None:
        self.countdown_var.set(str(max(0, seconds)))

    def hide(self) -> None:
        if self._activation_job is not None:
            try:
                self.master.after_cancel(self._activation_job)
            except Exception:
                pass
            self._activation_job = None
        if self._master_escape_bind_id is not None:
            try:
                self.master.unbind("<Escape>", self._master_escape_bind_id)
            except Exception:
                pass
            self._master_escape_bind_id = None
        for win in self.windows:
            try:
                win.destroy()
            except Exception:
                pass
        self.windows.clear()

    def _handle_escape(self, _event=None) -> str:
        self.on_skip()
        return "break"

    def _bind_master_escape(self) -> None:
        self._master_escape_bind_id = self.master.bind("<Escape>", self._handle_escape, add="+")

    def _activate_windows(self) -> None:
        for win in self.windows:
            try:
                if not win.winfo_exists():
                    continue
            except Exception:
                continue
            try:
                win.lift()
            except Exception:
                pass
            try:
                win.attributes("-topmost", True)
            except Exception:
                pass
            try:
                win.focus_force()
            except Exception:
                pass

    def _screen_specs(self) -> list[tuple[int, int, int, int]]:
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            user32 = ctypes.windll.user32
            monitors: list[tuple[int, int, int, int]] = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(RECT),
                wintypes.LPARAM,
            )

            def callback(_monitor, _hdc, rect_ptr, _data):
                rect = rect_ptr.contents
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                monitors.append((right - left, bottom - top, left, top))
                return True

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
