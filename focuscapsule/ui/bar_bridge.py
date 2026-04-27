"""QObject bridge between Python business logic and QML UI."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from focuscapsule.state import SessionRuntime, SessionState


def _format_countdown(sec: int) -> str:
    m, s = divmod(max(0, sec), 60)
    return f"{m:02d}:{s:02d}"


def _compute_progress(runtime: SessionRuntime) -> float:
    total = runtime.focus_total_sec
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - runtime.focus_remaining_sec / total))


def _config_to_map(config) -> dict:
    return {
        "total_minutes": config.total_minutes,
        "interval_min_minutes": config.interval_min_minutes,
        "interval_max_minutes": config.interval_max_minutes,
        "break_seconds": config.break_seconds,
        "finish_break_minutes": config.finish_break_minutes,
        "sound_enabled": config.sound_enabled,
    }


class BarBridge(QObject):
    snapshotChanged = pyqtSignal("QVariantMap")
    errorChanged = pyqtSignal(str)
    moveWindowX = pyqtSignal(int)
    commitWindowX = pyqtSignal(int)
    maskHeightChanged = pyqtSignal(int)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

    def push_snapshot(self, runtime: SessionRuntime, config, settings_open: bool = False):
        display_sec = (
            runtime.break_remaining_sec
            if runtime.state in (SessionState.MICRO_RESTING, SessionState.FINISH_RESTING)
            else runtime.focus_remaining_sec
        )
        snap = {
            "state": runtime.state.value,
            "countdown": _format_countdown(display_sec),
            "progress": _compute_progress(runtime),
            "draft": _config_to_map(config),
        }
        self.snapshotChanged.emit(snap)

    # ── QML → Python ─────────────────────────────────────────────────────────

    @pyqtSlot("QVariantMap")
    def startWithDraft(self, draft: dict):
        errors = self._app.start_session_with_draft(dict(draft))
        self.errorChanged.emit("\n".join(errors) if errors else "")

    @pyqtSlot()
    def endSession(self):
        self._app.end_session()

    @pyqtSlot()
    def quit(self):
        self._app.quit()

    @pyqtSlot(float)
    def moveBarX(self, x: float):
        self.moveWindowX.emit(int(x))

    @pyqtSlot(float)
    def saveBarX(self, x: float):
        self.commitWindowX.emit(int(x))

    def commit_bar_x(self, x: int) -> None:
        self._app.remember_bar_x(x)

    @pyqtSlot(float)
    def setVisibleHeight(self, h: float):
        self.maskHeightChanged.emit(int(h))
