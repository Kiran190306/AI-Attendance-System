import time
import pytest

from core.voice_engine import VoiceEngine
from core.audio import voice_validator


def test_verify_phrase():
    assert voice_validator.verify_phrase("present")
    assert voice_validator.verify_phrase("i'm here")
    assert not voice_validator.verify_phrase("hello")


def test_voice_engine_logging(tmp_path, monkeypatch):
    # use temporary log file to avoid polluting repo
    log_file = tmp_path / "voice_events.csv"
    engine = VoiceEngine(log_path=log_file)

    recorded = []

    def cb(name, command, status, valid):
        recorded.append((name, command, status, valid))

    # request with None raw_data (simulate missing mic) by monkeypatching recorder
    monkeypatch.setattr(
        "audio.voice_recorder.record_async", lambda cb_fn, duration=None: cb_fn(None)
    )
    engine.request("Alice", cb)
    time.sleep(0.1)

    assert recorded
    name, command, status, valid = recorded[0]
    assert name == "Alice"
    assert status == "No microphone"
    assert not valid
    # log file should exist and contain header + entry
    text = log_file.read_text()
    assert "student_name" in text
    assert "Alice" in text

