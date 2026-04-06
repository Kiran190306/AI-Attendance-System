"""Background worker that reads a single camera feed and forwards frames
for recognition and attendance.

The processor runs a tight loop in its own thread. It interacts with the
shared :class:`MultiCameraRecognitionEngine` which handles deduplication
across multiple streams. If an attendance callback is provided, it will be
invoked when the engine signals that a person should be marked.
"""
import logging
import threading
import time
from typing import Callable, Optional

import cv2

logger = logging.getLogger(__name__)


class StreamProcessorError(Exception):
    pass


class StreamProcessor:
    def __init__(
        self,
        camera_id: int,
        camera_name: str,
        engine,
        on_attendance: Optional[Callable[[str, float], None]] = None,
        target_fps: int = 15,
    ):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.engine = engine
        self.on_attendance = on_attendance
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps

        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = {"frames": 0, "marked": 0}

    def start(self) -> None:
        """Open camera and start processing thread."""
        self._cap = cv2.VideoCapture(self.camera_id)
        if not self._cap.isOpened():
            raise StreamProcessorError(
                f"Cannot open camera {self.camera_id} ({self.camera_name})"
            )
        logger.info("Camera connected: %s (id=%s)", self.camera_name, self.camera_id)
        # emit event via engine so listeners can see it
        try:
            self.engine.publish_event(
                "camera_connected", {"id": self.camera_id, "name": self.camera_name}
            )
        except Exception:
            pass

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop processing and release camera."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info("Camera disconnected: %s (id=%s)", self.camera_name, self.camera_id)
            try:
                self.engine.publish_event(
                    "camera_disconnected", {"id": self.camera_id, "name": self.camera_name}
                )
            except Exception:
                pass

    def _loop(self) -> None:
        while self._running and self._cap:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera %s", self.camera_name)
                continue

            results, display = self.engine.process_frame(self.camera_id, frame)

            # propagate attendance callbacks
            for res in results:
                if res.get("mark") and self.on_attendance:
                    try:
                        self.on_attendance(res.get("name"), res.get("confidence", 0.0))
                    except Exception as exc:
                        logger.error("attendance callback error: %s", exc)
                    self._stats["marked"] += 1

            self._stats["frames"] += 1
            # maintain target FPS
            time.sleep(self.frame_delay)

    def get_stats(self) -> dict:
        return self._stats.copy()
