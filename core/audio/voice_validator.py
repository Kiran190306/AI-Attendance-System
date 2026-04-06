from __future__ import annotations

import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

import core.config as config

# phrases defined in config
VALID_PHRASES = config.VALID_VOICE_PHRASES


def transcribe(raw_data: bytes) -> str | None:
    """Perform speech recognition on raw PCM audio bytes and return text."""
    r = sr.Recognizer()
    try:
        audio = sr.AudioData(raw_data, sample_rate=16000, sample_width=2)
        text = r.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        logger.info("could not understand audio")
    except Exception as exc:
        logger.warning("speech recognition error: %s", exc)
    return None


def verify_phrase(text: str | None) -> bool:
    if not text:
        return False
    for phrase in VALID_PHRASES:
        if phrase in text:
            return True
    return False


def verify_voice_identity(raw_data: bytes, student_name: str) -> bool:
    # stub: always return True; real system would create voice embeddings
    return True
