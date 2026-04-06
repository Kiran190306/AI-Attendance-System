"""Central recognition engine for multi-camera deployments.

This module wraps the standard face recognition engines and provides a
single entry point for all camera streams.  Its responsibilities include:

* Instantiating a dedicated face engine (or distance engine) per camera as
  needed.  Engines share underlying datasets so that embeddings are only
  loaded once when possible.
* Deduplicating attendance events so that a student seen on multiple
  cameras is only marked once per session.
* Emitting simple events (camera connection, disconnection) that other
  components can subscribe to (a lightweight event-bus).

The public API is intentionally small:

```
engine = MultiCameraRecognitionEngine(base_engine_cls=FaceRecognitionEngine)
engine.initialize()
results, display = engine.process_frame(camera_id, frame)
```"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from .face_engine import FaceRecognitionEngine
from .distance_recognition import DistanceRecognitionEngine

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def publish(self, event: str, payload: Any = None) -> None:
        for cb in self._listeners.get(event, []):
            try:
                cb(payload)
            except Exception as exc:
                logger.error("event listener raised: %s", exc)


class MultiCameraRecognitionEngineError(Exception):
    pass


class MultiCameraRecognitionEngine:
    def __init__(
        self,
        base_engine_cls: type = FaceRecognitionEngine,
        **engine_kwargs,
    ):
        # the engine class that will be instantiated per camera
        self.base_engine_cls = base_engine_cls
        self.engine_kwargs = engine_kwargs
        self._engines: Dict[int, Any] = {}
        self._global_marked: set[str] = set()
        self._lock = threading.Lock()
        self.events = EventBus()

    # delegate subscribe/publish so that external users do not need to know
    # about EventBus implementation.
    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        self.events.subscribe(event, callback)

    def publish_event(self, event: str, payload: Any = None) -> None:
        self.events.publish(event, {"event": event, "payload": payload})

    def initialize(self, camera_ids: Optional[List[int]] = None) -> None:
        """Pre-create engines for a list of camera IDs (optional)."""
        if camera_ids:
            for cid in camera_ids:
                if cid not in self._engines:
                    self._create_engine(cid)

    def _create_engine(self, camera_id: int) -> Any:
        try:
            engine = self.base_engine_cls(**self.engine_kwargs)
            engine.initialize()
            self._engines[camera_id] = engine
            logger.info("engine created for camera %s", camera_id)
            return engine
        except Exception as exc:
            logger.error("failed to initialize engine for camera %s: %s", camera_id, exc)
            raise MultiCameraRecognitionEngineError(exc)

    def _get_engine(self, camera_id: int) -> Any:
        if camera_id not in self._engines:
            return self._create_engine(camera_id)
        return self._engines[camera_id]

    def process_frame(
        self, camera_id: int, frame: Any
    ) -> Tuple[List[Dict], Any]:
        """Process a frame from a given camera.

        The returned ``results`` list mirrors the face engine API but may
        include an extra ``mark`` boolean field to indicate that the
        attendance service should add the person to the record.  ``mark`` is
        true only the first time a named student appears across all cameras
        during the current session.
        """
        engine = self._get_engine(camera_id)
        results, display = engine.process_frame(frame)

        with self._lock:
            for r in results:
                name = r.get("name")
                confidence = r.get("confidence", 0.0)
                r["mark"] = False
                if name and confidence > 0.65:
                    if name not in self._global_marked:
                        self._global_marked.add(name)
                        r["mark"] = True
        return results, display

    def get_global_stats(self) -> Dict:
        with self._lock:
            return {"unique_marked": len(self._global_marked)}

    def reset(self) -> None:
        """Reset the global attendance state (for a fresh session)."""
        with self._lock:
            self._global_marked.clear()

    def close(self) -> None:
        """Clean up any underlying engines."""
        for eng in self._engines.values():
            try:
                eng.close()
            except Exception:
                pass
        self._engines.clear()
