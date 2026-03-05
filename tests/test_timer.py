from focuscapsule.state import SessionRuntime
from focuscapsule.timer import MonotonicFocusTimer


def test_timer_basic_countdown() -> None:
    runtime = SessionRuntime(focus_total_sec=100)
    timer = MonotonicFocusTimer(runtime)
    timer.start(now=1000.0)
    assert timer.compute_focus_remaining(now=1012.4) == 88


def test_timer_rest_time_is_counted_in_focus() -> None:
    runtime = SessionRuntime(focus_total_sec=100)
    timer = MonotonicFocusTimer(runtime)
    timer.start(now=1000.0)

    timer.enter_rest(now=1010.0)
    timer.exit_rest(now=1015.0)

    # total elapsed is 20s, and rest time is also counted into focus
    assert timer.compute_focus_remaining(now=1020.0) == 80


def test_timer_focus_can_finish_while_resting() -> None:
    runtime = SessionRuntime(focus_total_sec=10)
    timer = MonotonicFocusTimer(runtime)
    timer.start(now=1000.0)

    timer.enter_rest(now=1006.0)
    assert timer.compute_focus_remaining(now=1010.0) == 0


def test_break_countdown_not_accelerated_by_tick_frequency() -> None:
    runtime = SessionRuntime()
    timer = MonotonicFocusTimer(runtime)
    timer.enter_rest(now=2000.0)

    # 200ms tick should not reduce one second each tick
    assert timer.compute_break_remaining(10, now=2000.2) == 10
    assert timer.compute_break_remaining(10, now=2000.8) == 10
    assert timer.compute_break_remaining(10, now=2001.0) == 9
    assert timer.compute_break_remaining(10, now=2009.0) == 1
    assert timer.compute_break_remaining(10, now=2010.1) == 0
