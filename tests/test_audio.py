import focuscapsule.audio as audio


class WinSoundStub:
    def __init__(self) -> None:
        self.beep_calls: list[tuple[int, int]] = []

    def Beep(self, frequency: int, duration: int) -> None:
        self.beep_calls.append((frequency, duration))


class ThreadStub:
    def __init__(self, target, args=(), daemon=None) -> None:
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False

    def start(self) -> None:
        self.started = True
        self.target(*self.args)


def test_audio_alert_patterns_cover_double_and_triple_beep_sequences(monkeypatch) -> None:
    stub = WinSoundStub()
    sleep_calls: list[float] = []
    monkeypatch.setattr(audio, "winsound", stub)
    monkeypatch.setattr(audio.time, "sleep", lambda seconds: sleep_calls.append(seconds))
    monkeypatch.setattr(audio.threading, "Thread", ThreadStub)

    audio.play_double_alert(True)
    audio.play_triple_alert(True)

    assert stub.beep_calls == [
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
        (audio.ALERT_FREQUENCY, audio.ALERT_DURATION_MS),
    ]
    assert sleep_calls == [
        audio.ALERT_GAP_MS / 1000.0,
        audio.ALERT_GAP_MS / 1000.0,
        audio.ALERT_GAP_MS / 1000.0,
    ]


def test_audio_alert_pattern_uses_background_thread(monkeypatch) -> None:
    started_threads: list[ThreadStub] = []

    class RecordingThread(ThreadStub):
        def __init__(self, target, args=(), daemon=None) -> None:
            super().__init__(target, args, daemon)
            started_threads.append(self)

    monkeypatch.setattr(audio.threading, "Thread", RecordingThread)
    monkeypatch.setattr(audio, "_play_pattern_sync", lambda count: None)

    audio.play_double_alert(True)

    assert len(started_threads) == 1
    assert started_threads[0].daemon is True
    assert started_threads[0].started is True
