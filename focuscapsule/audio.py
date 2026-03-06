from __future__ import annotations

import threading
import time

try:
    import winsound
except Exception:  # pragma: no cover
    winsound = None

ALERT_FREQUENCY = 880
ALERT_DURATION_MS = 150
ALERT_GAP_MS = 100


def _play_pattern_sync(count: int) -> None:
    if winsound is None:
        return
    for index in range(max(0, int(count))):
        winsound.Beep(ALERT_FREQUENCY, ALERT_DURATION_MS)
        if index < count - 1:
            time.sleep(ALERT_GAP_MS / 1000.0)


def _play_pattern(enabled: bool, count: int) -> None:
    if not enabled:
        return
    if winsound is None:
        return
    try:
        threading.Thread(
            target=_play_pattern_sync,
            args=(count,),
            daemon=True,
        ).start()
    except Exception:
        return


def play_alert(enabled: bool) -> None:
    _play_pattern(enabled, 1)


def play_double_alert(enabled: bool) -> None:
    _play_pattern(enabled, 2)


def play_triple_alert(enabled: bool) -> None:
    _play_pattern(enabled, 3)
