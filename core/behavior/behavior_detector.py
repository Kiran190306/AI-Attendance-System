from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2

import core.config as config
from .pose_analyzer import PoseAnalyzer
from .fight_detector import FightDetector
from .anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)


class BehaviorDetector:
    """Combines several sub-detectors into a single interface.

    Runs pose analysis every ``BEHAVIOR_FRAME_SKIP`` frames and keeps the
    latest classification so callers can simply query ``get_label`` for the
    current frame.
    """

    def __init__(self):
        self.pose = PoseAnalyzer()
        self.fight = FightDetector(aggression_threshold=config.BEHAVIOR_AGGRESSION_THRESHOLD)
        self.anomaly = AnomalyDetector()
        self._frame_count = 0
        self._last_result: Tuple[str, float] = ("NORMAL", 0.0)

    def process(self, frame: cv2.Mat, person_id: Optional[int], bbox: Tuple[int, int, int, int]) -> Tuple[str, float]:
        """Analyze ``frame`` (optionally constrained to ``bbox``) and return
        a tuple ``(label, confidence)``.
        """
        self._frame_count += 1
        if self._frame_count % config.BEHAVIOR_FRAME_SKIP != 0:
            return self._last_result

        roi = frame
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            roi = frame[y1:y2, x1:x2]

        pose_data = self.pose.analyze(roi)
        if pose_data is None:
            self._last_result = ("NORMAL", 0.0)
            return self._last_result

        fight_conf = self.fight.detect(pose_data)
        anomaly_conf = self.anomaly.analyze(person_id, bbox)

        # simple decision logic
        if fight_conf > 0.5:
            label, conf = ("AGGRESSIVE", fight_conf)
        elif anomaly_conf > 0:
            label, conf = ("SUSPICIOUS", anomaly_conf)
        else:
            label, conf = ("NORMAL", max(fight_conf, anomaly_conf))

        self._last_result = (label, conf)
        logger.debug("behavior label=%s conf=%.2f", label, conf)
        return self._last_result
