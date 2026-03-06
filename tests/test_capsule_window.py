from focuscapsule.ui.capsule_window import (
    DEFAULT_CAPSULE_HEIGHT,
    DEFAULT_CAPSULE_WIDTH,
    compute_bottom_right_position,
    compute_clamped_capsule_position,
    compute_default_capsule_position,
    compute_drag_position,
)


def test_compute_bottom_right_position_basic() -> None:
    x, y = compute_bottom_right_position(
        screen_width=1920,
        screen_height=1080,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        margin=24,
    )
    assert x == 1708
    assert y == 984


def test_compute_bottom_right_position_clamped() -> None:
    x, y = compute_bottom_right_position(
        screen_width=200,
        screen_height=100,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        margin=24,
    )
    assert x == 24
    assert y == 24


def test_compute_drag_position_uses_root_coordinates() -> None:
    x, y = compute_drag_position(
        window_x=100,
        window_y=200,
        current_root_x=430,
        current_root_y=560,
        previous_root_x=400,
        previous_root_y=500,
    )
    assert x == 130
    assert y == 260


def test_compute_drag_position_handles_negative_offset() -> None:
    x, y = compute_drag_position(
        window_x=-1200,
        window_y=80,
        current_root_x=360,
        current_root_y=200,
        previous_root_x=400,
        previous_root_y=160,
    )
    assert x == -1240
    assert y == 120


def test_compute_clamped_capsule_position_clamps_to_nearest_display() -> None:
    x, y = compute_clamped_capsule_position(
        x=6889,
        y=3845,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        display_bounds=[(0, 0, 1920, 1080)],
    )

    assert x == 1708
    assert y == 984


def test_compute_default_capsule_position_uses_primary_display_bounds() -> None:
    x, y = compute_default_capsule_position(
        screen_width=1920,
        screen_height=1080,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        display_bounds=[(-1600, 0, 0, 900), (0, 0, 1920, 1080)],
    )

    assert x == 1708
    assert y == 984
