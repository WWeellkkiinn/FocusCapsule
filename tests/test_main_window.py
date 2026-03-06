from focuscapsule.ui.main_window import (
    SHORT_INPUT_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    compute_center_position,
    compute_window_outer_size,
    compute_progress_ratio,
    format_countdown,
    format_minutes_preview,
    normalize_start_mode,
)


def test_format_countdown_clamps_negative_value() -> None:
    assert format_countdown(-3) == "00:00"


def test_format_countdown_formats_minutes_and_seconds() -> None:
    assert format_countdown(125) == "02:05"


def test_format_minutes_preview_updates_from_integer_text() -> None:
    assert format_minutes_preview("25") == "25:00"


def test_format_minutes_preview_uses_fallback_on_invalid_input() -> None:
    assert format_minutes_preview("abc", fallback_minutes=15) == "15:00"


def test_compute_progress_ratio_uses_focus_completion_ratio() -> None:
    assert compute_progress_ratio(75, 100) == 0.25


def test_compute_progress_ratio_handles_zero_total() -> None:
    assert compute_progress_ratio(0, 0) == 1.0


def test_normalize_start_mode_returns_capsule_unchanged() -> None:
    assert normalize_start_mode("capsule") == "capsule"


def test_normalize_start_mode_defaults_to_main_on_unrecognized_value() -> None:
    assert normalize_start_mode("unexpected") == "main"


def test_compute_center_position_returns_screen_center() -> None:
    assert compute_center_position(1920, 1080, WINDOW_WIDTH, WINDOW_HEIGHT) == (758, 360)


def test_compute_center_position_clamps_negative_position() -> None:
    assert compute_center_position(300, 200, WINDOW_WIDTH, WINDOW_HEIGHT) == (0, 0)


def test_compute_window_outer_size_includes_frame_and_titlebar() -> None:
    assert compute_window_outer_size(404, 360, 8, 31) == (420, 399)


def test_layout_constants_match_compact_form_design() -> None:
    assert WINDOW_WIDTH == 404
    assert WINDOW_HEIGHT == 360
    assert SHORT_INPUT_WIDTH == 62
