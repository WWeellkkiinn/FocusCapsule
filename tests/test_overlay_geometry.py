from focuscapsule.ui.overlay_window import OverlayWindow, _build_geometry, _scale_overlay_size


def test_geometry_negative_x() -> None:
    assert _build_geometry(1080, 1920, -1080, 0) == "1080x1920-1080+0"


def test_geometry_positive_x() -> None:
    assert _build_geometry(1920, 1080, 1080, 0) == "1920x1080+1080+0"


def test_geometry_negative_y() -> None:
    assert _build_geometry(1920, 1080, 0, -120) == "1920x1080+0-120"


def test_geometry_no_plus_minus_combo() -> None:
    geometry = _build_geometry(1080, 1920, -1080, -120)
    assert "+-" not in geometry


def test_scale_overlay_size_only_adjusts_dimensions_for_tk() -> None:
    assert _scale_overlay_size(3840, 144.0) == 2560


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

    def winfo_exists(self) -> bool:
        return self.exists

    def lift(self) -> None:
        self.lift_calls += 1

    def attributes(self, key: str, value: bool) -> None:
        self.attributes_calls.append((key, value))

    def focus_force(self) -> None:
        self.focus_calls += 1

    def destroy(self) -> None:
        self.destroy_calls += 1


def test_activate_windows_raises_overlay_to_topmost() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.windows = [OverlayWinStub(), OverlayWinStub(exists=False)]

    overlay._activate_windows()

    assert overlay.windows[0].lift_calls == 1
    assert overlay.windows[0].focus_calls == 1
    assert overlay.windows[0].attributes_calls == [("-topmost", True)]
    assert overlay.windows[1].lift_calls == 0


def test_hide_cleans_escape_binding_and_activation_job() -> None:
    overlay = OverlayWindow.__new__(OverlayWindow)
    overlay.master = OverlayMasterStub()
    overlay.windows = [OverlayWinStub()]
    overlay._master_escape_bind_id = "bind-1"
    overlay._activation_job = "after-1"

    overlay.hide()

    assert overlay.master.after_cancel_calls == ["after-1"]
    assert overlay.master.unbind_calls == [("<Escape>", "bind-1")]
    assert overlay.windows == []
