from focuscapsule.state import SessionConfig
from focuscapsule.ui.main_window import (
    SHORT_INPUT_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    MainSettingsWindow,
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
    assert compute_center_position(1920, 1080, WINDOW_WIDTH, WINDOW_HEIGHT) == (758, 344)
    assert compute_center_position(300, 200, WINDOW_WIDTH, WINDOW_HEIGHT) == (0, 0)
    assert compute_window_outer_size(404, 392, 8, 31) == (420, 431)


def test_main_window_layout_constants_match_compact_design() -> None:
    assert WINDOW_WIDTH == 404
    assert WINDOW_HEIGHT == 392
    assert SHORT_INPUT_WIDTH == 62


def test_main_window_start_click_reads_finish_break_minutes() -> None:
    captured: list[SessionConfig] = []
    window = MainSettingsWindow.__new__(MainSettingsWindow)
    window.total_minutes_var = type("Var", (), {"get": lambda self: "25"})()
    window.interval_min_var = type("Var", (), {"get": lambda self: "3"})()
    window.interval_max_var = type("Var", (), {"get": lambda self: "5"})()
    window.break_seconds_var = type("Var", (), {"get": lambda self: "10"})()
    window.finish_break_minutes_var = type("Var", (), {"get": lambda self: "7"})()
    window.sound_var = type("Var", (), {"get": lambda self: True})()
    window.capsule_mode_var = type("Var", (), {"get": lambda self: False})()
    window.error_var = type("Var", (), {"set": lambda self, value: None})()
    window.on_start = lambda config: captured.append(config)

    MainSettingsWindow._on_start_clicked(window)

    assert captured[0].finish_break_minutes == 7


def test_main_window_set_form_writes_finish_break_minutes() -> None:
    values: list[str] = []
    window = MainSettingsWindow.__new__(MainSettingsWindow)
    window.total_minutes_var = type("Var", (), {"set": lambda self, value: None})()
    window.interval_min_var = type("Var", (), {"set": lambda self, value: None})()
    window.interval_max_var = type("Var", (), {"set": lambda self, value: None})()
    window.break_seconds_var = type("Var", (), {"set": lambda self, value: None})()
    window.finish_break_minutes_var = type("Var", (), {"set": lambda self, value: values.append(value)})()
    window.sound_var = type("Var", (), {"set": lambda self, value: None})()
    window.capsule_mode_var = type("Var", (), {"set": lambda self, value: None})()
    window._update_preview_countdown = lambda: None

    MainSettingsWindow.set_form(window, SessionConfig(finish_break_minutes=9))

    assert values == ["9"]


def test_main_window_capsule_mode_change_notifies_owner() -> None:
    notified: list[str] = []
    window = MainSettingsWindow.__new__(MainSettingsWindow)
    window.on_start_mode_change = lambda mode: notified.append(mode)
    window.capsule_mode_var = type("Var", (), {"get": lambda self: True})()

    MainSettingsWindow._on_capsule_mode_changed(window)

    assert notified == ["capsule"]


def test_main_window_selected_start_mode_reflects_capsule_switch() -> None:
    window = MainSettingsWindow.__new__(MainSettingsWindow)
    window.capsule_mode_var = type("Var", (), {"get": lambda self: False})()

    assert MainSettingsWindow.selected_start_mode(window) == "main"
