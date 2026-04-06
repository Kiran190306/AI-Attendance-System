from __future__ import annotations

import threading
import logging
from typing import Optional

from .face_engine import FaceRecognitionEngine, FaceRecognitionEngineError

logger = logging.getLogger(__name__)


class SharedRecognitionEngine:
    """Singleton wrapper around :class:`FaceRecognitionEngine`.

    All camera threads access the same instance so that embeddings are loaded
    only once and memory is shared.  The initialize() call is executed lazily on
    first access.
    """

    _instance: Optional[FaceRecognitionEngine] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> FaceRecognitionEngine:
        with cls._lock:
            if cls._instance is None:
                try:
                    engine = FaceRecognitionEngine(target_frame_width=640)
                    engine.initialize()
                    cls._instance = engine
                    logger.info("shared recognition engine initialized")
                except FaceRecognitionEngineError as exc:
                    logger.error("failed to initialize shared engine: %s", exc)
                    raise
            return cls._instance

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None
                logger.info("shared recognition engine closed")
