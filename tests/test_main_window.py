from focuscapsule.ui.main_window import (
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


def test_normalize_start_mode_defaults_to_main() -> None:
    assert normalize_start_mode("capsule") == "capsule"
    assert normalize_start_mode("unexpected") == "main"
