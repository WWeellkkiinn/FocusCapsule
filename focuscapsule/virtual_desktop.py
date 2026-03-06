from __future__ import annotations

import ctypes
import sys
GA_ROOT = 2


def get_root_window_handle(hwnd: int) -> int:
    if sys.platform != "win32" or not hwnd:
        return int(hwnd)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    user32.GetAncestor.restype = ctypes.c_void_p
    root = user32.GetAncestor(ctypes.c_void_p(int(hwnd)), GA_ROOT)
    if root:
        return int(root)
    return int(hwnd)


class VirtualDesktopController:
    def __init__(self) -> None:
        self._enabled = sys.platform == "win32"
        self._app_view_cls = None
        self._desktop_cls = None
        if not self._enabled:
            return
        try:
            from pyvda import AppView, VirtualDesktop

            self._app_view_cls = AppView
            self._desktop_cls = VirtualDesktop
        except Exception:
            self._enabled = False

    @property
    def available(self) -> bool:
        return self._enabled and self._app_view_cls is not None and self._desktop_cls is not None

    def sync_window(self, hwnd: int) -> bool:
        if not self.available or not hwnd:
            return False
        target_hwnd = get_root_window_handle(hwnd)
        view = self._app_view_cls(hwnd=target_hwnd)
        if view.is_on_current_desktop():
            return False
        view.move(self._desktop_cls.current())
        return True

    def close(self) -> None:
        return
