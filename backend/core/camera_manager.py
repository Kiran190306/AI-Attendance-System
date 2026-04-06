import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable

from .stream_processor import StreamProcessor
from .multi_camera_recognition_engine import MultiCameraRecognitionEngine

logger = logging.getLogger(__name__)


class CameraManagerError(Exception):
    pass


class CameraManager:
    """Manage multiple camera streams using a shared recognition engine.

    The manager reads a JSON configuration that lists camera IDs and
    friendly names. It spins up a :class:`StreamProcessor` for each
    entry and keeps the processors running in background threads.

    An internal :class:`MultiCameraRecognitionEngine` is used so that
    attendance marking and analytics are de-duplicated across all feeds.
    """

    def __init__(self, config_path: Path | str = "config/cameras.json"):
        self.config_path = Path(config_path)
        self._load_config()
        self.processors: Dict[int, StreamProcessor] = {}
        # the recognition engine is shared by all streams
        self.engine = MultiCameraRecognitionEngine()
        self._running = False

        # optionally subscribers may watch for events
        self._event_listeners: Dict[str, List[Callable]] = {}

        # forward engine events to our listeners
        self.engine.subscribe("camera_connected", self._publish_event)
        self.engine.subscribe("camera_disconnected", self._publish_event)

    def _load_config(self) -> None:
        if not self.config_path.exists():
            logger.warning("Camera config not found: %s", self.config_path)
            self.cameras_config = {"cameras": []}
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.cameras_config = json.load(f)
        except Exception as exc:
            logger.error("Failed to parse camera config: %s", exc)
            self.cameras_config = {"cameras": []}

    def subscribe(self, event: str, callback: Callable) -> None:
        """Subscribe to manager-level events (same as engine events)."""
        self._event_listeners.setdefault(event, []).append(callback)

    def _publish_event(self, data: Optional[dict]) -> None:
        # engine passes a tuple (event_name, payload) when using subscribe
        if not data or not isinstance(data, dict):
            return
        event = data.get("event")
        payload = data.get("payload")
        if not event:
            return
        for cb in self._event_listeners.get(event, []):
            try:
                cb(payload)
            except Exception as ex:
                logger.error("listener error for %s: %s", event, ex)

    def start_all(
        self, on_attendance_marked: Optional[Callable[[str, float], None]] = None
    ) -> None:
        """Start stream processors for every camera in configuration."""
        self._running = True
        for cam in self.cameras_config.get("cameras", []):
            cam_id = cam.get("id")
            if cam_id is None:
                continue
            cam_name = cam.get("name", f"Camera_{cam_id}")
            try:
                proc = StreamProcessor(
                    camera_id=cam_id,
                    camera_name=cam_name,
                    engine=self.engine,
                    on_attendance=on_attendance_marked,
                )
                proc.start()
                self.processors[cam_id] = proc
                logger.info("Started processor for camera %s (id=%s)", cam_name, cam_id)
            except Exception as e:
                logger.error("Failed to start camera %s (%s): %s", cam_name, cam_id, e)

    def stop_all(self) -> None:
        """Stop all stream processors and release resources."""
        self._running = False
        for proc in list(self.processors.values()):
            proc.stop()
        self.processors.clear()
        logger.info("All cameras stopped")

    def get_stats(self) -> Dict:
        stats = {cam_id: proc.get_stats() for cam_id, proc in self.processors.items()}
        stats["global"] = self.engine.get_global_stats()
        return stats
