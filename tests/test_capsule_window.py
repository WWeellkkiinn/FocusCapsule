from focuscapsule.ui.capsule_window import (
    CapsuleWindow,
    DEFAULT_CAPSULE_HEIGHT,
    DEFAULT_CAPSULE_WIDTH,
    IDLE_TEXT,
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


def test_capsule_drag_only_reports_position_on_release() -> None:
    reported: list[tuple[int, int]] = []
    capsule = CapsuleWindow.__new__(CapsuleWindow)
    capsule._drag_root_x = 400
    capsule._drag_root_y = 500
    capsule._drag_moved = False
    capsule._restart_enabled = False
    capsule._release_suppressed_until_next_press = False
    capsule._pending_click_job = None
    capsule._on_position_change = lambda x, y: reported.append((x, y))
    current_position = {"x": 130, "y": 260}
    geometry_calls: list[str] = []

    def geometry(value: str) -> None:
        geometry_calls.append(value)
        x_str, y_str = value[1:].split("+")
        current_position["x"] = int(x_str)
        current_position["y"] = int(y_str)

    capsule.geometry = geometry
    capsule.winfo_x = lambda: current_position["x"]
    capsule.winfo_y = lambda: current_position["y"]

    event = type("Event", (), {"x_root": 430, "y_root": 560})()
    capsule._on_drag(event)
    assert reported == []

    capsule._on_left_release(None)
    assert geometry_calls == ["+160+320"]
    assert reported == [(160, 320)]


def test_capsule_idle_state_enables_start_click() -> None:
    started: list[str] = []
    capsule = CapsuleWindow.__new__(CapsuleWindow)
    capsule._pending_click_job = None
    capsule._restart_enabled = False
    capsule._start_enabled = False
    capsule.time_var = type("Var", (), {"set": lambda self, value: started.append(value)})()
    capsule.time_label = type("Label", (), {"configure": lambda self, **kwargs: None})()
    capsule.progress = type("Progress", (), {"set": lambda self, value: started.append(str(value))})()
    capsule._cancel_pending_click = lambda: None

    CapsuleWindow.show_idle_state(capsule)

    assert capsule._start_enabled is True
    assert capsule._restart_enabled is False
    assert started == [IDLE_TEXT, "0.0"]


def test_capsule_ctrl_click_suppresses_following_release_restart() -> None:
    capsule = CapsuleWindow.__new__(CapsuleWindow)
    capsule._pending_click_job = None
    capsule._restart_enabled = True
    capsule._start_enabled = False
    capsule._drag_moved = False
    capsule._release_suppressed_until_next_press = False
    finish_calls: list[str] = []
    restart_calls: list[str] = []
    capsule._cancel_pending_click = lambda: None
    capsule._finish_focus = lambda: finish_calls.append("finish")
    capsule.after = lambda delay, callback: restart_calls.append("scheduled") or "job-1"

    assert CapsuleWindow._on_ctrl_click(capsule, None) == "break"
    assert finish_calls == ["finish"]
    assert CapsuleWindow._on_left_release(capsule, None) == "break"
    assert restart_calls == []


def test_capsule_ctrl_click_still_suppresses_release_after_finished_state_transition() -> None:
    capsule = CapsuleWindow.__new__(CapsuleWindow)
    capsule._pending_click_job = None
    capsule._restart_enabled = False
    capsule._start_enabled = False
    capsule._drag_moved = False
    capsule._release_suppressed_until_next_press = False
    capsule._cancel_pending_click = lambda: None
    capsule.time_var = type("Var", (), {"set": lambda self, value: None})()
    capsule.time_label = type("Label", (), {"configure": lambda self, **kwargs: None})()
    capsule.progress = type("Progress", (), {"set": lambda self, value: None})()
    finish_calls: list[str] = []
    restart_calls: list[str] = []

    def finish_focus() -> None:
        finish_calls.append("finish")
        CapsuleWindow.show_finished_state(capsule)

    capsule._finish_focus = finish_focus
    capsule.after = lambda delay, callback: restart_calls.append("scheduled") or "job-1"

    CapsuleWindow._on_ctrl_click(capsule, None)
    assert finish_calls == ["finish"]
    assert capsule._restart_enabled is True
    assert CapsuleWindow._on_left_release(capsule, None) == "break"
    assert CapsuleWindow._on_left_release(capsule, None) == "break"
    assert restart_calls == []

    CapsuleWindow._start_drag(capsule, type("Event", (), {"x_root": 1, "y_root": 2})())
    assert capsule._release_suppressed_until_next_press is False
