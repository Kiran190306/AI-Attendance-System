from __future__ import annotations

import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from . import config
from .audio import voice_recorder, voice_validator

logger = logging.getLogger(__name__)


class VoiceEngineError(Exception):
    pass


class VoiceEngine:
    """Handles asynchronous voice capture, transcription and identity verification.

    The engine also keeps a CSV log of voice events and prevents duplicate
    concurrent requests for the same student.
    """

    def __init__(self, log_path: Path | str = config.VOICE_LOG_CSV):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv_headers()
        # names currently being processed
        self.pending: set[str] = set()

    # ------------------------------------------------------------------
    # logging helpers
    # ------------------------------------------------------------------

    def _ensure_csv_headers(self) -> None:
        if self.log_path.exists():
            return
        try:
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["student_name", "timestamp", "voice_command", "status"],
                )
                writer.writeheader()
            logger.info("created voice log csv with headers")
        except Exception as exc:
            logger.error("failed to create voice log headers: %s", exc)

    def _write_log(
        self, student_name: str, timestamp: str, command: str, status: str
    ) -> None:
        try:
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["student_name", "timestamp", "voice_command", "status"],
                )
                writer.writerow(
                    {
                        "student_name": student_name,
                        "timestamp": timestamp,
                        "voice_command": command,
                        "status": status,
                    }
                )
        except Exception as exc:
            logger.warning("failed to write voice log: %s", exc)

    # ------------------------------------------------------------------
    # processing helpers
    # ------------------------------------------------------------------

    def _analyze(self, student_name: str, raw_data: Optional[bytes]) -> tuple[str, str, bool]:
        # returns (command, status, valid)
        if raw_data is None:
            status = "No microphone"
            self._write_log(student_name, datetime.now().isoformat(), "", status)
            return "", status, False

        # transcribe audio
        text = voice_validator.transcribe(raw_data)
        phrase_ok = voice_validator.verify_phrase(text)
        voice_ok = voice_validator.verify_voice_identity(raw_data, student_name)

        if not phrase_ok:
            status = "Phrase not recognized"
        elif not voice_ok:
            status = "Voice mismatch"
        else:
            status = "OK"

        command = text or ""
        self._write_log(student_name, datetime.now().isoformat(), command, status)
        return command, status, phrase_ok and voice_ok

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def request(
        self,
        student_name: str,
        callback: Callable[[str, str, str, bool], None],
        duration: float | None = None,
    ) -> None:
        """Trigger a non-blocking voice recording for ``student_name``.

        ``callback`` will be invoked once processing finishes using signature
        ``callback(name, command, status, valid)``.
        """
        if student_name in self.pending:
            return
        self.pending.add(student_name)
        rec_duration = duration or config.VOICE_RECORD_DURATION

        def _finished(raw_data: Optional[bytes]) -> None:
            # remove from pending regardless of outcome
            self.pending.discard(student_name)
            cmd, status, valid = self._analyze(student_name, raw_data)
            try:
                callback(student_name, cmd, status, valid)
            except Exception as exc:  # pragma: no cover - user callback error
                logger.exception("voice callback error for %s: %s", student_name, exc)

        voice_recorder.record_async(_finished, duration=rec_duration)
