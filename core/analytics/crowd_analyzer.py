from __future__ import annotations

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import Any, Dict, List

from .density_estimator import classify as classify_density
from .heatmap_generator import HeatmapGenerator
from ..tracking.movement_tracker import MovementTracker

logger = logging.getLogger(__name__)


class CrowdAnalyzer:
    """Per-frame crowd analytics using simple people detection and tracking.

    This class is designed to be called from each camera thread; it maintains
    internal state (heatmap, movement tracks) separately for each instance.
    """

    def __init__(self, frame_skip: int = 3, target_width: int = 640) -> None:
        # HOG person detector
        self.detector = cv2.HOGDescriptor()
        self.detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.heatmap = HeatmapGenerator()
        self.tracker = MovementTracker()
        self.frame_skip = frame_skip
        self._counter = 0
        self.target_width = target_width
        # log file for crowd alerts
        self.alert_log = "logs/crowd_alerts.csv"
        import os
        os.makedirs("logs", exist_ok=True)
        # ensure CSV header exists
        if not os.path.exists(self.alert_log):
            with open(self.alert_log, "w", encoding="utf-8") as f:
                f.write("camera_id,timestamp,crowd_count,alert_type\n")

    def _detect_people(self, frame: np.ndarray) -> List[tuple[int, int, int, int]]:
        # resize for speed
        h, w = frame.shape[:2]
        if w > self.target_width:
            scale = self.target_width / w
            frame = cv2.resize(frame, (self.target_width, int(h * scale)))
        rects, weights = self.detector.detectMultiScale(frame, winStride=(8,8))
        boxes = []
        for (x, y, w, h) in rects:
            boxes.append((x, y, x + w, y + h))
        return boxes

    def _log_alert(self, camera_id: str, count: int, alert_type: str) -> None:
        ts = datetime.now().isoformat()
        try:
            with open(self.alert_log, "a", encoding="utf-8") as f:
                f.write(f"{camera_id},{ts},{count},{alert_type}\n")
        except Exception:
            logger.warning("failed to write crowd alert")

    def analyze(self, frame: np.ndarray, camera_id: str) -> Dict[str, Any]:
        """Run analytics on a frame and return stats/overlays.

        Returns a dict containing:
            count, density, heatmap_overlay, alerts(list),
            entry_rate, exit_rate, avg_dwell
        """
        self._counter += 1
        if self._counter % self.frame_skip != 0:
            return {}

        boxes = self._detect_people(frame)
        count = len(boxes)

        density = classify_density(count)
        if density == "High":
            self._log_alert(camera_id, count, "overcrowding")
        # simplistic sudden increase alert if count > previous *2
        # (could be improved with history)
        if hasattr(self, "_last_count") and count > self._last_count * 2:
            self._log_alert(camera_id, count, "sudden_increase")
        self._last_count = count

        # update heatmap and movement tracker
        self.heatmap.update(frame, boxes)
        self.tracker.update(boxes)

        heat_overlay = self.heatmap.overlay(frame)

        alerts: List[Dict[str, Any]] = []
        # we logged them above; for return provide simple list
        if density == "High":
            alerts.append({"type": "overcrowding", "count": count})

        return {
            "count": count,
            "density": density,
            "heatmap_overlay": heat_overlay,
            "alerts": alerts,
            "entry_rate": self.tracker.entry_rate,
            "exit_rate": self.tracker.exit_rate,
            "avg_dwell": self.tracker.avg_dwell,
        }
