"""Qt window management for the FocusCapsule bottom bar."""
from __future__ import annotations
import ctypes
import os
import sys
from pathlib import Path

import PyQt6
from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from focuscapsule.ui.win32_bar import set_bottom_bar_mask, setup_toolwindow

_QT6_QML_DIR = os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "qml")
_QML_PATH = Path(__file__).with_name("bar.qml")

_BASE_BAR_W = 280
_BASE_BAR_H = 20
_SNAP_THRESHOLD = 40  # logical px from edge — snap to center when released within this distance


def _primary_ag():
    """Primary screen available geometry as (x, y, w, h) in Qt logical pixels."""
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 0, 0, 1920, 1080  # safe fallback — should never happen
    ag = screen.availableGeometry()
    return ag.x(), ag.y(), ag.width(), ag.height()


def _get_ui_scale() -> float:
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
        self._pending_visible_h: int = 0
        self._snap_anim: QPropertyAnimation | None = None

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

    # ── Window setup ──────────────────────────────────────────────────────────

    def _position_window(self):
        ax, ay, aw, ah = _primary_ag()
        x = self._saved_x if self._saved_x is not None else ax + (aw - self._bar_w) // 2
        x = max(ax, min(x, ax + aw - self._bar_w))
        self._win.setX(x)
        self._win.setY(ay)
        self._win.setWidth(self._bar_w)
        self._win.setHeight(ah)

    def _setup_win32(self):
        self._own_hwnd = int(self._win.winId())
        setup_toolwindow(self._own_hwnd)
        self._apply_mask(self._pending_visible_h if self._pending_visible_h else self._bar_h)

    def _apply_mask(self, visible_h: int):
        self._pending_visible_h = visible_h
        if not self._own_hwnd:
            return
        set_bottom_bar_mask(
            hwnd=self._own_hwnd,
            window_h_logical=int(self._win.height()),
            visible_h_logical=visible_h,
            window_w_logical=self._bar_w,
        )

    # ── Drag — follows mouse directly, no animation ───────────────────────────

    def _move_window_x(self, x: int):
        # Stop any running snap animation so it doesn't fight the drag
        try:
            if self._snap_anim and self._snap_anim.state() != QAbstractAnimation.State.Stopped:
                self._snap_anim.stop()
        except RuntimeError:
            self._snap_anim = None
        ax, _ay, aw, _ah = _primary_ag()
        clamped = max(ax, min(x, ax + aw - self._bar_w))
        self._win.setX(clamped)

    # ── Release / snap — animated ─────────────────────────────────────────────

    def _commit_window_x(self, x: int):
        ax, _ay, aw, _ah = _primary_ag()
        center_x = ax + (aw - self._bar_w) // 2

        # Left or right edge snap → center
        if x <= ax + _SNAP_THRESHOLD or x >= ax + aw - self._bar_w - _SNAP_THRESHOLD:
            self._animate_to_x(center_x)
            self._bridge.commit_bar_x(center_x)
            return

        clamped = max(ax, min(x, ax + aw - self._bar_w))
        self._bridge.commit_bar_x(clamped)

    def _animate_to_x(self, target_x: int) -> QPropertyAnimation:
        try:
            if self._snap_anim:
                self._snap_anim.stop()
        except RuntimeError:
            pass
        finally:
            self._snap_anim = None
        try:
            anim = QPropertyAnimation(self._win, b"x")
            anim.setDuration(250)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setEndValue(target_x)
            anim.finished.connect(lambda: setattr(self, "_snap_anim", None))
            anim.start()
            self._snap_anim = anim
            return anim
        except RuntimeError:
            return QPropertyAnimation()  # no-op placeholder

    # ── Public ────────────────────────────────────────────────────────────────

    def own_hwnd(self) -> int:
        return self._own_hwnd
