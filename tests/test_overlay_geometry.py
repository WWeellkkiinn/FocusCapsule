from focuscapsule.ui.overlay_window import _build_geometry


def test_geometry_negative_x() -> None:
    assert _build_geometry(1080, 1920, -1080, 0) == "1080x1920-1080+0"


def test_geometry_positive_x() -> None:
    assert _build_geometry(1920, 1080, 1080, 0) == "1920x1080+1080+0"


def test_geometry_negative_y() -> None:
    assert _build_geometry(1920, 1080, 0, -120) == "1920x1080+0-120"


def test_geometry_no_plus_minus_combo() -> None:
    geometry = _build_geometry(1080, 1920, -1080, -120)
    assert "+-" not in geometry
