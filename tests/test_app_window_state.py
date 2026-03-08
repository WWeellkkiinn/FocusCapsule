from focuscapsule.app import FocusCapsuleApp
from focuscapsule.state import SessionConfig, SessionRuntime, SessionState


class VirtualDesktopStub:
    def __init__(self) -> None:
        self.synced_hwnds: list[int] = []
        self.close_calls = 0

    def sync_window(self, hwnd: int) -> bool:
        self.synced_hwnds.append(hwnd)
        return True

    def close(self) -> None:
        self.close_calls += 1


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
        self.hwnd = 9527
        self.call_order: list[str] = []

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
        self.call_order.append("deiconify")

    def attributes(self, key: str, value: bool) -> None:
        self.topmost_values.append((key, value))

    def set_default_position(self, margin: int = 24, preferred_position: tuple[int, int] | None = None) -> None:
        self.default_position_calls += 1
        self.default_position_args.append(preferred_position)
        self.call_order.append("position")

    def update_view(self, remaining_sec: int, total_sec: int) -> None:
        self.updated.append((remaining_sec, total_sec))

    def show_finished_state(self) -> None:
        self.finished_state_calls += 1

    def native_handle(self) -> int:
        return self.hwnd


class OverlayStub:
    def __init__(self) -> None:
        self.hide_calls = 0
        self.show_calls: list[dict] = []

    def hide(self) -> None:
        self.hide_calls += 1

    def show(self, seconds: int, title: str, hint: str) -> None:
        self.show_calls.append({"seconds": seconds, "title": title, "hint": hint})


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
    app._virtual_desktop = VirtualDesktopStub()
    app._last_virtual_desktop_sync_at = 0.0
    return app


def test_app_window_mode_switching_covers_main_and_capsule_paths() -> None:
    from_main = build_app()
    from_main.switch_to_capsule_mode()
    assert from_main.current_mode == "capsule"
    assert from_main.main_window.withdraw_calls == 1
    assert from_main.capsule.state() == "normal"

    back_to_main = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    back_to_main.current_mode = "capsule"
    back_to_main.show_main_window()
    assert back_to_main.current_mode == "main"
    assert back_to_main.capsule.state() == "withdrawn"
    assert back_to_main.main_window.session_view_calls == 1

    already_capsule = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    already_capsule.current_mode = "capsule"
    already_capsule.switch_to_capsule_mode()
    assert already_capsule.main_window.withdraw_calls == 0
    assert already_capsule.capsule.state() == "normal"


def test_app_start_session_covers_mode_seed_and_saved_position_preservation(monkeypatch) -> None:
    app = build_app(state=SessionState.IDLE)
    app.config = SessionConfig(capsule_x=-1280, capsule_y=88)
    app.timer = TimerStub()
    calls: list[str] = []
    saved_configs: list[SessionConfig] = []
    captured_kwargs: dict = {}
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: saved_configs.append(config))
    monkeypatch.setattr(
        "focuscapsule.app.build_trigger_points",
        lambda **kwargs: captured_kwargs.update(kwargs) or [],
    )
    monkeypatch.setattr("focuscapsule.app.MonotonicFocusTimer", lambda runtime: app.timer)
    monkeypatch.setattr(app, "_ensure_capsule", lambda: app.capsule)
    monkeypatch.setattr(app, "_show_capsule_mode", lambda: calls.append("capsule"))
    monkeypatch.setattr(app, "_show_main_mode", lambda: calls.append("main"))
    monkeypatch.setattr(app, "_schedule_tick", lambda: calls.append("tick"))

    app.start_session(SessionConfig(start_mode="capsule", seed=123))

    assert app.current_mode == "capsule"
    assert app.timer.started is True
    assert captured_kwargs["seed"] is None
    assert saved_configs[0].capsule_x == -1280
    assert saved_configs[0].capsule_y == 88
    assert calls == ["capsule", "tick"]


def test_app_close_and_finish_paths_cover_config_and_capsule_end_states(monkeypatch) -> None:
    close_app = build_app(capsule_state="normal")
    close_alerts: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_triple_alert", lambda enabled: close_alerts.append(enabled))
    close_app._close_session("已完成")
    assert close_app.runtime.state == SessionState.FINISHED
    assert close_app.overlay.hide_calls == 1
    assert close_app.capsule.state() == "withdrawn"
    assert close_app.main_window.config_status_messages == ["已完成"]
    assert close_app.main_window.after_cancel_calls == ["job-1"]
    assert close_alerts == [True]


def test_app_finished_capsule_paths_cover_show_main_and_restart(monkeypatch) -> None:
    show_main_app = build_app(state=SessionState.FINISHED, capsule_state="normal")
    show_main_app.current_mode = "capsule"
    show_main_app.show_main_window()
    assert show_main_app.current_mode == "main"
    assert show_main_app.capsule.state() == "withdrawn"
    assert show_main_app.main_window.config_status_messages == ["本次专注已完成。"]

    restart_app = build_app(state=SessionState.FINISHED, capsule_state="normal")
    restart_app.current_mode = "capsule"
    restarted: list[SessionConfig] = []
    monkeypatch.setattr(restart_app, "start_session", lambda config: restarted.append(config))
    restart_app.restart_finished_session()
    assert restarted[0].start_mode == "capsule"


def test_app_capsule_position_paths_cover_show_save_validate_and_launch_normalize(monkeypatch) -> None:
    app = build_app()
    app.config = SessionConfig(capsule_x=6889, capsule_y=3845)
    app._display_bounds = lambda: [(-1600, 0, 0, 900), (0, 0, 1920, 1080)]

    validated = app._validated_capsule_position()
    assert validated == (1708, 984)

    saved_configs: list[SessionConfig] = []
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: saved_configs.append(config))
    app._normalize_capsule_position_on_launch()
    assert app.config.capsule_x == 1708
    assert app.config.capsule_y == 984

    app.config = SessionConfig(capsule_x=-1440, capsule_y=120)
    app.current_mode = "capsule"
    app._show_capsule()
    assert app.capsule.default_position_args[-1] == (-1440, 120)
    assert app._virtual_desktop.synced_hwnds == [9527]
    assert app.capsule.call_order[:2] == ["position", "deiconify"]

    app.remember_capsule_position(-1330, 96)
    assert app.config.capsule_x == -1330
    assert app.config.capsule_y == 96
    assert saved_configs[-1].capsule_x == -1330


def test_app_position_save_tolerates_oserror(monkeypatch) -> None:
    app = build_app()
    monkeypatch.setattr("focuscapsule.app.save_config", lambda config: (_ for _ in ()).throw(OSError("disk")))

    app.remember_capsule_position(120, 180)

    assert app.config.capsule_x == 120
    assert app.config.capsule_y == 180


def test_app_virtual_desktop_sync_is_rate_limited_and_forceable(monkeypatch) -> None:
    app = build_app(capsule_state="normal")
    app.current_mode = "capsule"
    times = iter([10.0, 10.2, 11.5, 11.7])
    monkeypatch.setattr("focuscapsule.app.time.monotonic", lambda: next(times))

    app._sync_capsule_virtual_desktop()
    app._sync_capsule_virtual_desktop()
    app._sync_capsule_virtual_desktop()
    app._sync_capsule_virtual_desktop(force=True)

    assert app._virtual_desktop.synced_hwnds == [9527, 9527, 9527]


def test_app_shutdown_releases_virtual_desktop_controller() -> None:
    app = build_app(capsule_state="normal")
    destroyed = {"called": 0}

    def destroy_capsule() -> None:
        destroyed["called"] += 1

    app.capsule.destroy = destroy_capsule
    app.main_window.destroy = lambda: None

    app._shutdown()

    assert destroyed["called"] == 1
    assert app._virtual_desktop.close_calls == 1


def test_app_rest_transition_paths_cover_overlay_and_sound(monkeypatch) -> None:
    enter_app = build_app()
    enter_alerts: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_double_alert", lambda enabled: enter_alerts.append(enabled))
    monkeypatch.setattr(enter_app, "_schedule_tick", lambda: None)
    enter_app.enter_micro_rest()
    assert enter_app.runtime.state == SessionState.MICRO_RESTING
    assert enter_app.timer.enter_rest_calls == 1
    assert enter_app.overlay.show_calls == [
        {
            "seconds": enter_app.config.break_seconds,
            "title": "微休息时间：请转动脖子、闭眼深呼吸",
            "hint": "按 Esc 键可跳过本次休息",
        }
    ]
    assert enter_alerts == [True]

    exit_app = build_app(state=SessionState.MICRO_RESTING)
    exit_alerts: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_double_alert", lambda enabled: exit_alerts.append(enabled))
    monkeypatch.setattr(exit_app, "_apply_display_mode", lambda: None)
    monkeypatch.setattr(exit_app, "_schedule_tick", lambda: None)
    exit_app.exit_micro_rest("timeout")
    assert exit_app.runtime.state == SessionState.FOCUSING
    assert exit_app.overlay.hide_calls == 1
    assert exit_app.timer.exit_rest_calls == 1
    assert exit_alerts == [True]


def test_app_finish_rest_paths_cover_enter_skip_and_timeout(monkeypatch) -> None:
    finish_app = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    finish_app.current_mode = "capsule"
    finish_alerts: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_triple_alert", lambda enabled: finish_alerts.append(enabled))
    monkeypatch.setattr(finish_app, "_schedule_tick", lambda: None)

    finish_app.enter_finish_rest()

    assert finish_app.runtime.state == SessionState.FINISH_RESTING
    assert finish_app.runtime.focus_remaining_sec == 0
    assert finish_app.current_mode == "main"
    assert finish_app.capsule.state() == "withdrawn"
    assert finish_app.main_window.session_view_calls == 1
    assert finish_app.main_window.lift_calls == 0
    assert finish_app.main_window.focus_calls == 0
    assert finish_app.overlay.show_calls == [
        {
            "seconds": finish_app.config.finish_break_minutes * 60,
            "title": "专注结束：请离开屏幕，放松休息",
            "hint": "按 Esc 键可提前结束本次休息",
        }
    ]
    assert finish_alerts == [True]

    skip_app = build_app(state=SessionState.FINISH_RESTING)
    completed: list[str] = []
    monkeypatch.setattr(skip_app, "complete_finish_rest", lambda reason: completed.append(reason))
    skip_app.skip_rest()
    assert completed == ["esc"]

    timeout_app = build_app(state=SessionState.FINISH_RESTING)
    timeout_app.tick_job = "job-2"
    close_alerts: list[bool] = []
    monkeypatch.setattr("focuscapsule.app.play_triple_alert", lambda enabled: close_alerts.append(enabled))

    timeout_app.complete_finish_rest("timeout")

    assert timeout_app.runtime.state == SessionState.FINISHED
    assert timeout_app.overlay.hide_calls == 1
    assert timeout_app.main_window.config_status_messages == ["本次专注已完成。"]
    assert close_alerts == []


def test_app_finish_session_enters_finish_rest_instead_of_closing(monkeypatch) -> None:
    app = build_app(state=SessionState.FOCUSING, capsule_state="normal")
    entered: list[str] = []
    monkeypatch.setattr(app, "enter_finish_rest", lambda: entered.append("finish_rest"))

    app.finish_session()

    assert entered == ["finish_rest"]


def test_app_end_session_early_still_closes_without_finish_rest(monkeypatch) -> None:
    app = build_app(state=SessionState.FOCUSING)
    closed: list[str] = []
    monkeypatch.setattr(app, "_close_session", lambda message, play_sound=True: closed.append(message))

    app.end_session_early()

    assert closed == ["已提前结束本次专注。"]
