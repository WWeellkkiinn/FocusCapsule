"""Qt window management for the FocusCapsule bottom bar."""
from __future__ import annotations
import ctypes
import os
import sys
from pathlib import Path

import PyQt6
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from focuscapsule.ui.win32_bar import set_bottom_bar_mask, setup_toolwindow

_QT6_QML_DIR = os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "qml")
_QML_PATH = Path(__file__).with_name("bar.qml")

_BASE_BAR_W = 280
_BASE_BAR_H = 20


def _get_ui_scale() -> float:
    """Softened DPI scale, matching VibeBar's formula.
    100% → 1.0, 150% → 1.25, 200% → 1.5
    """
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        win_scale = max(dpi, 96) / 96.0
        return 1.0 + (win_scale - 1.0) * 0.5
    except Exception:
        return 1.0


class BarWindow:
    def __init__(self, bridge, saved_x: int | None = None):
        self._bridge = bridge
        self._saved_x = saved_x
        self._own_hwnd = 0

        sf = _get_ui_scale()
        self._bar_w = int(_BASE_BAR_W * sf)
        self._bar_h = int(_BASE_BAR_H * sf)

        self._engine = QQmlApplicationEngine()
        if os.path.isdir(_QT6_QML_DIR):
            self._engine.addImportPath(_QT6_QML_DIR)
        ctx = self._engine.rootContext()
        ctx.setContextProperty("bridge", bridge)
        ctx.setContextProperty("scaleFactor", float(sf))
        self._engine.load(str(_QML_PATH))

        roots = self._engine.rootObjects()
        if not roots:
            print("[FocusCapsule] QML failed to load", file=sys.stderr)
            sys.exit(1)
        self._win = roots[0]

        self._position_window()

        bridge.moveWindowX.connect(self._move_window_x)
        bridge.commitWindowX.connect(self._commit_window_x)
        bridge.maskHeightChanged.connect(self._apply_mask)

        QTimer.singleShot(150, self._setup_win32)

    def _position_window(self):
        screen = QGuiApplication.primaryScreen()
        ag = screen.availableGeometry()

        x = self._saved_x if self._saved_x is not None else ag.x() + (ag.width() - self._bar_w) // 2
        x = max(ag.x(), min(x, ag.x() + ag.width() - self._bar_w))

        self._win.setX(x)
        self._win.setY(ag.y())
        self._win.setWidth(self._bar_w)
        self._win.setHeight(ag.height())

    def _setup_win32(self):
        self._own_hwnd = int(self._win.winId())
        setup_toolwindow(self._own_hwnd)
        self._apply_mask(self._bar_h)

    def _apply_mask(self, visible_h: int):
        if not self._own_hwnd:
            return
        set_bottom_bar_mask(
            hwnd=self._own_hwnd,
            window_h_logical=int(self._win.height()),
            visible_h_logical=visible_h,
            window_w_logical=self._bar_w,
        )

    def _move_window_x(self, x: int):
        screen = QGuiApplication.primaryScreen()
        ag = screen.availableGeometry()
        clamped = max(ag.x(), min(x, ag.x() + ag.width() - self._bar_w))
        self._win.setX(clamped)

    def _commit_window_x(self, x: int):
        screen = QGuiApplication.primaryScreen()
        ag = screen.availableGeometry()
        clamped = max(ag.x(), min(x, ag.x() + ag.width() - self._bar_w))
        self._bridge.commit_bar_x(clamped)

    def own_hwnd(self) -> int:
        return self._own_hwnd
