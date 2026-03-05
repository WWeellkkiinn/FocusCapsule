from __future__ import annotations


try:
    import winsound
except Exception:  # pragma: no cover
    winsound = None


def play_alert(enabled: bool) -> None:
    if not enabled:
        return
    if winsound is None:
        return
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        return
