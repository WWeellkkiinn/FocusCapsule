from focuscapsule.app import FocusCapsuleApp
from focuscapsule.state import SessionConfig, SessionRuntime, SessionState


class MainWindowStub:
    def __init__(self) -> None:
        self.updated: list[dict] = []
        self.session_view_calls = 0
        self.config_view_calls = 0
        self.config_status_messages: list[str] = []
        self.deiconify_calls = 0
        self.withdraw_calls = 0
        self.lift_calls = 0
        self.focus_calls = 0
        self.after_cancel_calls: list[str] = []
        self.errors: list[str] = []
        self.screen_width = 1920
        self.screen_height = 1080

    def update_session_view(self, **kwargs) -> None:
        self.updated.append(kwargs)

    def show_session_view(self) -> None:
        self.session_view_calls += 1

    def show_config_view(self, status_message: str = "准备开始专注") -> None:
        self.config_view_calls += 1
        self.config_status_messages.append(status_message)

    def show_error(self, text: str) -> None:
        self.errors.append(text)

    def deiconify(self) -> None:
        self.deiconify_calls += 1

    def withdraw(self) -> None:
        self.withdraw_calls += 1

    def lift(self) -> None:
        self.lift_calls += 1

    def focus_force(self) -> None:
        self.focus_calls += 1

    def after_cancel(self, job) -> None:
        self.after_cancel_calls.append(job)

    def winfo_screenwidth(self) -> int:
        return self.screen_width

    def winfo_screenheight(self) -> int:
        return self.screen_height


class CapsuleStub:
    def __init__(self, state: str = "withdrawn") -> None:
        self._state = state
        self.withdraw_calls = 0
        self.deiconify_calls = 0
        self.topmost_values: list[tuple[str, bool]] = []
        self.default_position_calls = 0
        self.default_position_args: list[tuple[int, int] | None] = []
        self.updated: list[tuple[int, int]] = []
        self.finished_state_calls = 0

    def winfo_exists(self) -> bool:
        return True

    def state(self) -> str:
        return self._state

    def withdraw(self) -> None:
        self._state = "withdrawn"
        self.withdraw_calls += 1

    def deiconify(self) -> None:
        self._state = "normal"
        self.deiconify_calls += 1

    def attributes(self, key: str, value: bool) -> None:
        self.topmost_values.append((key, value))

    def set_default_position(self, margin: int = 24, preferred_position: tuple[int, int] | None = None) -> None:
        self.default_position_calls += 1
        self.default_position_args.append(preferred_position)

    def update_view(self, remaining_sec: int, total_sec: int) -> None:
        self.updated.append((remaining_sec, total_sec))

    def show_finished_state(self) -> None:
        self.finished_state_calls += 1


class OverlayStub:
    def __init__(self) -> None:
        self.hide_calls = 0
        self.show_calls: list[int] = []

    def hide(self) -> None:
        self.hide_calls += 1

    def show(self, seconds: int) -> None:
        self.show_calls.append(seconds)


class TimerStub:
    def __init__(self) -> None:
        self.started = False
        self.enter_rest_calls = 0
        self.exit_rest_calls = 0

    def start(self) -> None:
        self.started = True

    def enter_rest(self) -> None:
        self.enter_rest_calls += 1

    def exit_rest(self) -> None:
        self.exit_rest_calls += 1


def build_app(state: SessionState = SessionState.FOCUSING, capsule_state: str = "withdrawn") -> FocusCapsuleApp:
    app = FocusCapsuleApp.__new__(FocusCapsuleApp)
    app.config = SessionConfig()
    app.runtime = SessionRuntime(
        state=state,
        focus_total_sec=1500,
        focus_remaining_sec=1200,
        break_remaining_sec=10,
    )
    app.main_window = MainWindowStub()
    app.capsule = CapsuleStub(capsule_state)
    app.overlay = OverlayStub()
    app.tick_job = "job-1"
    app.current_mode = "main"
    app.timer = TimerStub()
    app._last_finish_message = "本次专注已完成。"
    return app


def test_switch_to_capsule_mode_switches_from_main_to_capsule() -> None:
    app = build_app()

    app.switch_to_capsule_mode()
    assert app.current_mode == "capsule"
    assert app.main_window.withdraw_calls == 1
    assert app.capsule.state() == "normal"


def test_show_main_window_hides_capsule_and_restores_main_only() -> None:
    app = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    app.current_mode = "capsule"

    app.show_main_window()

    assert app.current_mode == "main"
    assert app.capsule.state() == "withdrawn"
    assert app.main_window.session_view_calls == 1
    assert app.main_window.deiconify_calls == 1


def test_switch_to_capsule_mode_keeps_capsule_state_when_already_in_capsule() -> None:
    app = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    app.current_mode = "capsule"

    app.switch_to_capsule_mode()

    assert app.current_mode == "capsule"
    assert app.main_window.withdraw_calls == 0
    assert app.capsule.state() == "normal"


def test_start_session_uses_selected_capsule_mode(monkeypatch) -> None:
    app = build_app(state=SessionState.IDLE)
    app.main_window = MainWindowStub()
    app.timer = TimerStub()
    calls: list[str] = []
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: None)
    monkeypatch.setattr("focuscapsule.app.build_trigger_points", lambda **kwargs: [])
    monkeypatch.setattr("focuscapsule.app.MonotonicFocusTimer", lambda runtime: app.timer)
    monkeypatch.setattr(app, "_ensure_capsule", lambda: app.capsule)
    monkeypatch.setattr(app, "_show_capsule_mode", lambda: calls.append("capsule"))
    monkeypatch.setattr(app, "_show_main_mode", lambda: calls.append("main"))
    monkeypatch.setattr(app, "_schedule_tick", lambda: calls.append("tick"))

    config = SessionConfig(start_mode="capsule")
    app.start_session(config)

    assert app.current_mode == "capsule"
    assert app.timer.started is True
    assert calls == ["capsule", "tick"]


def test_start_session_ignores_seed_from_config_and_uses_automatic_random(monkeypatch) -> None:
    app = build_app(state=SessionState.IDLE)
    app.main_window = MainWindowStub()
    app.timer = TimerStub()
    captured_kwargs: dict = {}
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: None)
    monkeypatch.setattr(
        "focuscapsule.app.build_trigger_points",
        lambda **kwargs: captured_kwargs.update(kwargs) or [],
    )
    monkeypatch.setattr("focuscapsule.app.MonotonicFocusTimer", lambda runtime: app.timer)
    monkeypatch.setattr(app, "_ensure_capsule", lambda: app.capsule)
    monkeypatch.setattr(app, "_show_capsule_mode", lambda: None)
    monkeypatch.setattr(app, "_show_main_mode", lambda: None)
    monkeypatch.setattr(app, "_schedule_tick", lambda: None)

    app.start_session(SessionConfig(seed=123))

    assert captured_kwargs["seed"] is None


def test_start_session_preserves_saved_capsule_position(monkeypatch) -> None:
    app = build_app(state=SessionState.IDLE)
    app.main_window = MainWindowStub()
    app.timer = TimerStub()
    app.config = SessionConfig(capsule_x=-1280, capsule_y=88)
    saved_configs: list[SessionConfig] = []
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: saved_configs.append(config))
    monkeypatch.setattr("focuscapsule.app.build_trigger_points", lambda **kwargs: [])
    monkeypatch.setattr("focuscapsule.app.MonotonicFocusTimer", lambda runtime: app.timer)
    monkeypatch.setattr(app, "_ensure_capsule", lambda: app.capsule)
    monkeypatch.setattr(app, "_show_capsule_mode", lambda: None)
    monkeypatch.setattr(app, "_show_main_mode", lambda: None)
    monkeypatch.setattr(app, "_schedule_tick", lambda: None)

    app.start_session(SessionConfig(start_mode="capsule"))

    assert app.config.capsule_x == -1280
    assert app.config.capsule_y == 88
    assert saved_configs
    assert saved_configs[0].capsule_x == -1280
    assert saved_configs[0].capsule_y == 88


def test_close_session_returns_to_config_view_and_clears_overlays() -> None:
    app = build_app(capsule_state="normal")

    app._close_session("已完成")

    assert app.runtime.state == SessionState.FINISHED
    assert app.overlay.hide_calls == 1
    assert app.capsule.state() == "withdrawn"
    assert app.main_window.config_view_calls == 1
    assert app.main_window.config_status_messages == ["已完成"]
    assert app.main_window.after_cancel_calls == ["job-1"]


def test_finish_session_keeps_capsule_visible_and_restartable_in_capsule_mode() -> None:
    app = build_app(capsule_state="normal")
    app.current_mode = "capsule"

    app.finish_session()

    assert app.runtime.state == SessionState.FINISHED
    assert app.overlay.hide_calls == 1
    assert app.main_window.after_cancel_calls == ["job-1"]
    assert app.main_window.config_view_calls == 1
    assert app.main_window.deiconify_calls == 0
    assert app.capsule.finished_state_calls == 1
    assert app.capsule.state() == "normal"


def test_show_main_window_from_finished_capsule_shows_config_view() -> None:
    app = build_app(state=SessionState.FINISHED, capsule_state="normal")
    app.current_mode = "capsule"
    app._last_finish_message = "本次专注已完成。"

    app.show_main_window()

    assert app.current_mode == "main"
    assert app.capsule.state() == "withdrawn"
    assert app.main_window.config_view_calls == 1
    assert app.main_window.config_status_messages == ["本次专注已完成。"]
    assert app.main_window.deiconify_calls == 1


def test_restart_finished_session_restarts_in_capsule_mode(monkeypatch) -> None:
    app = build_app(state=SessionState.FINISHED, capsule_state="normal")
    app.current_mode = "capsule"
    restarted: list[SessionConfig] = []
    monkeypatch.setattr(app, "start_session", lambda config: restarted.append(config))

    app.restart_finished_session()

    assert restarted
    assert restarted[0].start_mode == "capsule"


def test_show_capsule_uses_saved_position_when_available() -> None:
    app = build_app()
    app.config = SessionConfig(capsule_x=-1440, capsule_y=120)
    app._display_bounds = lambda: [(-1600, 0, 0, 900), (0, 0, 1920, 1080)]

    app._show_capsule()

    assert app.capsule.default_position_calls == 1
    assert app.capsule.default_position_args == [(-1440, 120)]


def test_remember_capsule_position_updates_config_and_saves(monkeypatch) -> None:
    app = build_app()
    saved_configs: list[SessionConfig] = []
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: saved_configs.append(config))

    app.remember_capsule_position(-1330, 96)

    assert app.config.capsule_x == -1330
    assert app.config.capsule_y == 96
    assert saved_configs
    assert saved_configs[0].capsule_x == -1330
    assert saved_configs[0].capsule_y == 96


def test_enter_rest_plays_alert(monkeypatch) -> None:
    app = build_app()
    played: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_double_alert", lambda enabled: played.append(enabled))
    monkeypatch.setattr(app, "_schedule_tick", lambda: None)

    app.enter_rest()

    assert played == [True]


def test_exit_rest_plays_alert(monkeypatch) -> None:
    app = build_app(state=SessionState.RESTING)
    played: list[bool] = []
    app.timer = type("RestTimerStub", (), {"exit_rest": lambda self: None})()
    monkeypatch.setattr("focuscapsule.app.play_double_alert", lambda enabled: played.append(enabled))
    monkeypatch.setattr(app, "_apply_display_mode", lambda: None)
    monkeypatch.setattr(app, "_schedule_tick", lambda: None)

    app.exit_rest("timeout")

    assert played == [True]


def test_finish_session_in_capsule_mode_plays_alert(monkeypatch) -> None:
    app = build_app(capsule_state="normal")
    app.current_mode = "capsule"
    played: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_triple_alert", lambda enabled: played.append(enabled))

    app.finish_session()

    assert played == [True]


def test_close_session_plays_alert(monkeypatch) -> None:
    app = build_app(capsule_state="normal")
    played: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_triple_alert", lambda enabled: played.append(enabled))

    app._close_session("已完成")

    assert played == [True]


def test_validated_capsule_position_clamps_out_of_range_saved_value() -> None:
    app = build_app()
    app.config = SessionConfig(capsule_x=6889, capsule_y=3845)
    app._display_bounds = lambda: [(0, 0, 1920, 1080)]

    position = app._validated_capsule_position()

    assert position == (1708, 984)


def test_normalize_capsule_position_on_launch_updates_config_and_saves(monkeypatch) -> None:
    app = build_app()
    app.config = SessionConfig(capsule_x=6889, capsule_y=3845)
    saved_configs: list[SessionConfig] = []
    app._display_bounds = lambda: [(0, 0, 1920, 1080)]
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: saved_configs.append(config))

    app._normalize_capsule_position_on_launch()

    assert app.config.capsule_x == 1708
    assert app.config.capsule_y == 984
    assert saved_configs
    assert saved_configs[0].capsule_x == 1708
    assert saved_configs[0].capsule_y == 984
