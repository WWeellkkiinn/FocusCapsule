from focuscapsule.state import SessionRuntime
from focuscapsule.timer import MonotonicFocusTimer


def test_timer_focus_remaining_covers_basic_resting_and_finish_cases() -> None:
    runtime = SessionRuntime(focus_total_sec=100)
    timer = MonotonicFocusTimer(runtime)
    timer.start(now=1000.0)

    assert timer.compute_focus_remaining(now=1012.4) == 88

    timer.enter_rest(now=1010.0)
    timer.exit_rest()
    assert timer.compute_focus_remaining(now=1020.0) == 80

    short_runtime = SessionRuntime(focus_total_sec=10)
    short_timer = MonotonicFocusTimer(short_runtime)
    short_timer.start(now=1000.0)
    short_timer.enter_rest(now=1006.0)
    assert short_timer.compute_focus_remaining(now=1010.0) == 0


def test_timer_break_countdown_is_stable_across_tick_frequency() -> None:
    runtime = SessionRuntime()
    timer = MonotonicFocusTimer(runtime)
    timer.enter_rest(now=2000.0)

    assert timer.compute_break_remaining(10, now=2000.2) == 10
    assert timer.compute_break_remaining(10, now=2000.8) == 10
    assert timer.compute_break_remaining(10, now=2001.0) == 9
    assert timer.compute_break_remaining(10, now=2009.0) == 1
    assert timer.compute_break_remaining(10, now=2010.1) == 0
