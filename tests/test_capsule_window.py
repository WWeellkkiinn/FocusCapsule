from focuscapsule.ui.capsule_window import compute_bottom_right_position


def test_compute_bottom_right_position_basic() -> None:
    x, y = compute_bottom_right_position(
        screen_width=1920,
        screen_height=1080,
        window_width=280,
        window_height=120,
        margin=24,
    )
    assert x == 1616
    assert y == 936


def test_compute_bottom_right_position_clamped() -> None:
    x, y = compute_bottom_right_position(
        screen_width=200,
        screen_height=100,
        window_width=280,
        window_height=120,
        margin=24,
    )
    assert x == 24
    assert y == 24
