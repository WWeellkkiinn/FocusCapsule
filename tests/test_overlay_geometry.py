from focuscapsule.ui.overlay_window import (
    OverlayWindow,
    _build_geometry,
    _format_countdown,
    _scale_overlay_size,
)


def test_overlay_geometry_helpers_cover_signs_and_dpi_scaling() -> None:
    assert _build_geometry(1080, 1920, -1080, 0) == "1080x1920-1080+0"
    assert _build_geometry(1920, 1080, 1080, 0) == "1920x1080+1080+0"
    assert _build_geometry(1920, 1080, 0, -120) == "1920x1080+0-120"
    assert "+-" not in _build_geometry(1080, 1920, -1080, -120)
    assert _scale_overlay_size(3840, 144.0) == 2560
    geometry = _build_geometry(
        _scale_overlay_size(1440, 144.0),
        _scale_overlay_size(2560, 144.0),
        -1440,
        0,
    )
    assert geometry == "960x1707-1440+0"
    assert _format_countdown(300) == "05:00"
    assert _format_countdown(9) == "00:09"


class OverlayMasterStub:
    def __init__(self) -> None:
        self.bind_calls: list[tuple[str, object, str]] = []
        self.unbind_calls: list[tuple[str, str]] = []
        self.after_calls: list[tuple[int, object]] = []
        self.after_cancel_calls: list[str] = []

    def bind(self, sequence: str, callback, add: str | None = None) -> str:
        self.bind_calls.append((sequence, callback, add or ""))
        return "bind-1"

    def unbind(self, sequence: str, funcid: str | None = None) -> None:
        self.unbind_calls.append((sequence, funcid or ""))

    def after(self, delay_ms: int, callback):
        self.after_calls.append((delay_ms, callback))
        return "after-1"

    def after_cancel(self, job_id: str) -> None:
        self.after_cancel_calls.append(job_id)


class OverlayWinStub:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.lift_calls = 0
        self.focus_calls = 0
        self.attributes_calls: list[tuple[str, bool]] = []
        self.destroy_calls = 0
        self.update_calls = 0
        self.grab_set_calls = 0
        self.grab_set_global_calls = 0
        self.grab_release_calls = 0

    def winfo_exists(self) -> bool:
        return self.exists

    def update_idletasks(self) -> None:
        self.update_calls += 1

    def lift(self) -> None:
        self.lift_calls += 1

    def attributes(self, key: str, value: bool) -> None:
        self.attributes_calls.append((key, value))

    def focus_force(self) -> None:
        self.focus_calls += 1

    def grab_set(self) -> None:
        self.grab_set_calls += 1

    def grab_set_global(self) -> None:
        self.grab_set_global_calls += 1

    def grab_release(self) -> None:
        self.grab_release_calls += 1

    def destroy(self) -> None:
        self.destroy_calls += 1


def test_overlay_activate_windows_only_touches_existing_windows() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.windows = [OverlayWinStub(), OverlayWinStub(exists=False)]

    overlay._activate_windows()

    assert overlay.windows[0].lift_calls == 1
    assert overlay.windows[0].focus_calls == 1
    assert overlay.windows[0].attributes_calls == [("-topmost", True)]
    assert overlay.windows[1].lift_calls == 0


def test_overlay_hide_cleans_bindings_jobs_and_windows() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.master = OverlayMasterStub()
    overlay.windows = [OverlayWinStub()]
    overlay._master_escape_bind_id = "bind-1"
    overlay._activation_job = "after-1"
    overlay._grab_window = overlay.windows[0]
    overlay._escape_monitor_stop = None

    overlay.hide()

    assert overlay.master.after_cancel_calls == ["after-1"]
    assert overlay.master.unbind_calls == [("<Escape>", "bind-1")]
    assert overlay.windows == []
    assert overlay._grab_window is None


def test_overlay_claim_keyboard_focus_prefers_first_window() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.windows = [OverlayWinStub(), OverlayWinStub()]
    overlay._grab_window = None
    overlay._activate_window = lambda win: None

    overlay._claim_keyboard_focus()

    assert overlay._grab_window is overlay.windows[0]
    assert overlay.windows[0].update_calls == 1
    assert overlay.windows[0].grab_set_global_calls == 1
    assert overlay.windows[0].focus_calls == 1


def test_overlay_schedule_activation_refresh_retries_until_budget_exhausted() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.master = OverlayMasterStub()
    overlay._activation_attempts_remaining = 1
    activate_calls: list[str] = []
    overlay._activate_windows = lambda: activate_calls.append("tick")

    overlay._schedule_activation_refresh()

    assert activate_calls == ["tick"]
    assert overlay._activation_attempts_remaining == 0
    assert overlay._activation_job == "after-1"


def test_overlay_request_skip_once_only_calls_handler_once() -> None:
    calls: list[str] = []
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay._skip_requested = False
    overlay.on_skip = lambda: calls.append("skip")

    overlay._request_skip_once()
    overlay._request_skip_once()

    assert calls == ["skip"]


def test_overlay_start_escape_monitor_spawns_windows_poll_thread(monkeypatch) -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay._escape_monitor_stop = None
    overlay._stop_escape_monitor = lambda: None

    started: list[tuple[tuple, bool]] = []

    class ThreadStub:
        def __init__(self, target, args=(), daemon=None) -> None:
            started.append((args, bool(daemon)))

        def start(self) -> None:
            return None

    monkeypatch.setattr("focuscapsule.ui.overlay_window.sys.platform", "win32")
    monkeypatch.setattr("focuscapsule.ui.overlay_window.threading.Thread", ThreadStub)

    overlay._start_escape_monitor()

    assert overlay._escape_monitor_stop is not None
    assert len(started) == 1
    assert started[0][1] is True
