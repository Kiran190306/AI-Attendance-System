from __future__ import annotations

import json
import threading
import math
import logging
from pathlib import Path
from typing import List, Dict, Any

import cv2
import numpy as np

from .stream_processor import StreamProcessor
from .recognition_engine import SharedRecognitionEngine
from .tracker import Tracker
from .events.event_bus import EventBus

logger = logging.getLogger(__name__)


class CameraManager:
    """Loads camera configuration and starts a thread for each source.

    A small display thread composes individual feeds into a grid so the user
    can see all cameras at once.  Each ``StreamProcessor`` is responsible for
    detection/recognition and event publication.
    """

    def __init__(
        self,
        config_path: Path | str = "config/cameras.json",
        engine: SharedRecognitionEngine | None = None,
        tracker: Tracker | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.engine = engine or SharedRecognitionEngine.get()
        self.tracker = tracker or Tracker()
        self.bus = event_bus or EventBus()
        self._proc_threads: Dict[str, StreamProcessor] = {}
        self._display_thread: threading.Thread | None = None
        self._running = False

        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"camera config not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.cameras: List[Dict[str, Any]] = data.get("cameras", [])

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def start_all(self) -> None:
        logger.info("starting camera manager with %d cameras", len(self.cameras))
        # ensure camera event log folder exists
        import os
        os.makedirs("logs", exist_ok=True)
        self.bus.start()
        for cam in self.cameras:
            cam_id = cam.get("id")
            source = cam.get("source")
            if cam_id in self._proc_threads:
                continue
            proc = StreamProcessor(
                camera_id=cam_id,
                source=source,
                engine=self.engine,
                tracker=self.tracker,
                event_bus=self.bus,
            )
            proc.start()
            self._proc_threads[cam_id] = proc
        self._running = True
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()

    def stop_all(self) -> None:
        logger.info("stopping camera manager")
        self._running = False
        for proc in self._proc_threads.values():
            proc.stop()
        self.bus.stop()
        if self._display_thread:
            self._display_thread.join()
        cv2.destroyAllWindows()

    # ------------------------------------------------------------------
    # display helpers
    # ------------------------------------------------------------------

    def _make_grid(self, frames: List[Any]) -> Any:
        # build roughly square grid
        n = len(frames)
        if n == 0:
            return None
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / cols))
        # ensure all frames same size
        h, w = frames[0].shape[:2]
        # pad missing
        grid_frames = []
        for r in range(rows):
            row_frames = []
            for c in range(cols):
                idx = r * cols + c
                if idx < n:
                    row_frames.append(frames[idx])
                else:
                    row_frames.append(255 * np.ones((h, w, 3), dtype=np.uint8))
            grid_frames.append(cv2.hconcat(row_frames))
        return cv2.vconcat(grid_frames)

    def _display_loop(self) -> None:
        while self._running:
            frames = []
            for proc in self._proc_threads.values():
                if proc.last_display is not None:
                    frames.append(proc.last_display)
            if frames:
                grid = self._make_grid(frames)
                if grid is not None:
                    cv2.imshow("Multi-Camera Attendance", grid)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("quit requested from display window")
                self.stop_all()
                break
            # small sleep to avoid busy loop
            threading.Event().wait(0.03)
