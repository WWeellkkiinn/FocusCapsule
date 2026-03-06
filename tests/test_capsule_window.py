from focuscapsule.ui.capsule_window import (
    DEFAULT_CAPSULE_HEIGHT,
    DEFAULT_CAPSULE_WIDTH,
    compute_bottom_right_position,
    compute_clamped_capsule_position,
    compute_default_capsule_position,
    compute_drag_position,
)


def test_capsule_position_helpers_cover_default_and_clamped_layout() -> None:
    assert compute_bottom_right_position(1920, 1080, DEFAULT_CAPSULE_WIDTH, DEFAULT_CAPSULE_HEIGHT, 24) == (1708, 984)
    assert compute_bottom_right_position(200, 100, DEFAULT_CAPSULE_WIDTH, DEFAULT_CAPSULE_HEIGHT, 24) == (24, 24)
    assert compute_default_capsule_position(
        screen_width=1920,
        screen_height=1080,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        display_bounds=[(-1600, 0, 0, 900), (0, 0, 1920, 1080)],
    ) == (1708, 984)
    assert compute_clamped_capsule_position(
        x=6889,
        y=3845,
        window_width=DEFAULT_CAPSULE_WIDTH,
        window_height=DEFAULT_CAPSULE_HEIGHT,
        display_bounds=[(0, 0, 1920, 1080)],
    ) == (1708, 984)


def test_capsule_drag_position_uses_root_coordinates_in_normal_case() -> None:
    assert compute_drag_position(
        window_x=100,
        window_y=200,
        current_root_x=430,
        current_root_y=560,
        previous_root_x=400,
        previous_root_y=500,
    ) == (130, 260)


def test_capsule_drag_position_handles_negative_offset_case() -> None:
    assert compute_drag_position(
        window_x=-1200,
        window_y=80,
        current_root_x=360,
        current_root_y=200,
        previous_root_x=400,
        previous_root_y=160,
    ) == (-1240, 120)
