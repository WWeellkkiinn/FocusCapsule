import focuscapsule.audio as audio


class WinSoundStub:
    def __init__(self) -> None:
        self.beep_calls: list[tuple[int, int]] = []

    def Beep(self, frequency: int, duration: int) -> None:
        self.beep_calls.append((frequency, duration))

def test_play_double_alert_beeps_twice(monkeypatch) -> None:
    stub = WinSoundStub()
    sleep_calls: list[float] = []
    monkeypatch.setattr(audio, "winsound", stub)
    monkeypatch.setattr(audio.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    audio.play_double_alert(True)

    assert stub.beep_calls == [
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
    ]
    assert sleep_calls == [audio.ALERT_GAP_MS / 1000.0]


def test_play_triple_alert_beeps_three_times(monkeypatch) -> None:
    stub = WinSoundStub()
    sleep_calls: list[float] = []
    monkeypatch.setattr(audio, "winsound", stub)
    monkeypatch.setattr(audio.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    audio.play_triple_alert(True)

    assert stub.beep_calls == [
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
    ]
    assert sleep_calls == [audio.ALERT_GAP_MS / 1000.0, audio.ALERT_GAP_MS / 1000.0]
