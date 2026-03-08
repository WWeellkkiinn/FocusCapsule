from __future__ import annotations

import customtkinter as ctk

OVERLAY_BG_COLOR = "#000000"
OVERLAY_TITLE_COLOR = "#F8FAFC"
OVERLAY_COUNTDOWN_COLOR = "#FFFFFF"
OVERLAY_HINT_COLOR = "#DCE7F5"
OVERLAY_ALPHA = 0.80


def _build_geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{int(width)}x{int(height)}{int(x):+d}{int(y):+d}"


def _format_countdown(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    return f"{minutes:02d}:{secs:02d}"


def _scale_overlay_size(size: int, pixels_per_inch: float) -> int:
    if pixels_per_inch <= 0:
        return int(size)
    return max(1, int(round(int(size) * 96.0 / float(pixels_per_inch))))


class OverlayWindow:
    def __init__(self, master: ctk.CTk, on_skip) -> None:
        self.master = master
        self.on_skip = on_skip
        self.windows: list[ctk.CTkToplevel] = []
        self.countdown_var = ctk.StringVar(value="00:10")
        self.title_var = ctk.StringVar(value="微休息时间：请转动脖子、闭眼深呼吸")
        self.hint_var = ctk.StringVar(value="按 Esc 键可跳过本次休息")
        self._master_escape_bind_id: str | None = None
        self._activation_job = None
        self._grab_window: ctk.CTkToplevel | None = None

    def show(self, seconds: int, title: str, hint: str) -> None:
        self.hide()
        self.countdown_var.set(_format_countdown(seconds))
        self.title_var.set(title)
        self.hint_var.set(hint)
        screen_specs = self._screen_specs()

        for width, height, x, y in screen_specs:
            win = ctk.CTkToplevel(self.master)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                win.attributes("-alpha", OVERLAY_ALPHA)
            except Exception:
                pass
            win.geometry(_build_geometry(width, height, x, y))
            win.configure(fg_color=OVERLAY_BG_COLOR)
            win.bind("<Escape>", self._handle_escape)
            center_layer = ctk.CTkFrame(win, fg_color="transparent")
            center_layer.pack(fill="both", expand=True)
            center_layer.grid_rowconfigure(0, weight=1)
            center_layer.grid_columnconfigure(0, weight=1)

            frame = ctk.CTkFrame(center_layer, fg_color="transparent")

            ctk.CTkLabel(
                frame,
                textvariable=self.title_var,
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
                textvariable=self.hint_var,
                font=("Microsoft YaHei", 16),
                text_color=OVERLAY_HINT_COLOR,
            ).pack(pady=(16, 0))
            frame.grid(row=0, column=0)

            self.windows.append(win)

        self._bind_master_escape()
        self._claim_keyboard_focus()
        self._activate_windows()
        self._activation_job = self.master.after(80, self._activate_windows)

    def update_countdown(self, seconds: int) -> None:
        self.countdown_var.set(_format_countdown(seconds))

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
        if self._grab_window is not None:
            try:
                self._grab_window.grab_release()
            except Exception:
                pass
            self._grab_window = None
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

    def _claim_keyboard_focus(self) -> None:
        if not self.windows:
            return
        self._grab_window = self.windows[0]
        try:
            self._grab_window.update_idletasks()
        except Exception:
            pass
        try:
            self._grab_window.grab_set()
        except Exception:
            pass
        try:
            self._grab_window.focus_force()
        except Exception:
            pass

    def _activate_windows(self) -> None:
        for win in self.windows:
            try:
                if not win.winfo_exists():
                    continue
            except Exception:
                continue
            try:
                win.update_idletasks()
            except Exception:
                pass
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
            try:
                shcore = ctypes.windll.shcore
            except Exception:
                shcore = None

            monitors: list[tuple[int, int, int, int]] = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(RECT),
                wintypes.LPARAM,
            )

            MDT_EFFECTIVE_DPI = 0

            def callback(monitor, _hdc, rect_ptr, _data):
                rect = rect_ptr.contents
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

                # Retrieve per-monitor effective DPI (Windows 8.1+).
                # Falls back to 96 (1:1 mapping) when shcore is unavailable.
                dpi = 96.0
                if shcore is not None:
                    try:
                        dpi_x = wintypes.UINT(0)
                        dpi_y = wintypes.UINT(0)
                        shcore.GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                        if dpi_x.value > 0:
                            dpi = float(dpi_x.value)
                    except Exception:
                        pass

                # Tk 在当前 DPI 感知模式下会放大窗口尺寸，但不会同样放大窗口坐标。
                # 因此这里只修正 width/height，x/y 保持显示器原始坐标。
                log_w = _scale_overlay_size(right - left, dpi)
                log_h = _scale_overlay_size(bottom - top, dpi)
                monitors.append((log_w, log_h, left, top))
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
