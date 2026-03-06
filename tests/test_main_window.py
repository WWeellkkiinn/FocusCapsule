from focuscapsule.ui.main_window import (
    SHORT_INPUT_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    compute_center_position,
    compute_progress_ratio,
    compute_window_outer_size,
    format_countdown,
    format_minutes_preview,
    normalize_start_mode,
)


def test_main_window_formatting_helpers_cover_valid_and_fallback_cases() -> None:
    assert format_countdown(-3) == "00:00"
    assert format_countdown(125) == "02:05"
    assert format_minutes_preview("25") == "25:00"
    assert format_minutes_preview("abc", fallback_minutes=15) == "15:00"


def test_main_window_progress_and_mode_helpers_cover_core_paths() -> None:
    assert compute_progress_ratio(75, 100) == 0.25
    assert compute_progress_ratio(0, 0) == 1.0
    assert normalize_start_mode("capsule") == "capsule"
    assert normalize_start_mode("unexpected") == "main"


def test_main_window_geometry_helpers_cover_normal_and_clamped_layout() -> None:
    assert compute_center_position(1920, 1080, WINDOW_WIDTH, WINDOW_HEIGHT) == (758, 360)
    assert compute_center_position(300, 200, WINDOW_WIDTH, WINDOW_HEIGHT) == (0, 0)
    assert compute_window_outer_size(404, 360, 8, 31) == (420, 399)


def test_main_window_layout_constants_match_compact_design() -> None:
    assert WINDOW_WIDTH == 404
    assert WINDOW_HEIGHT == 360
    assert SHORT_INPUT_WIDTH == 62
