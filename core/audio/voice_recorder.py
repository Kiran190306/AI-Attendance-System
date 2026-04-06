from __future__ import annotations

import speech_recognition as sr
import threading
import time
import logging

logger = logging.getLogger(__name__)


def record_clip(duration: float = 3.0) -> bytes | None:
    """Record a short audio clip from default microphone and return raw data.

    Runs synchronously (blocking) for ``duration`` seconds.  Returns ``None``
    if recording fails (e.g. no microphone).
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logger.debug("adjusting for ambient noise")
            r.adjust_for_ambient_noise(source, duration=0.5)
            logger.debug("recording for %.1f seconds", duration)
            audio = r.record(source, duration=duration)
            return audio.get_raw_data()
    except Exception as e:
        logger.warning("voice recorder error: %s", e)
        return None


def record_async(callback: callable, duration: float = 3.0) -> None:
    """Start background thread that records clip then invokes ``callback(data)``."""
    def _worker():
        data = record_clip(duration=duration)
        callback(data)
    th = threading.Thread(target=_worker, daemon=True)
    th.start()
