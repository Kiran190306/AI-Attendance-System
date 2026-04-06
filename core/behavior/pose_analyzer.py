from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import cv2
import numpy as np
import mediapipe as mp

logger = logging.getLogger(__name__)


class PoseAnalyzer:
    """Wrapper around MediaPipe Pose to extract key landmark information.

    The class is lightweight and can be reused across frames.  We provide a
    simple ``analyze`` method that returns a dictionary of landmark positions
    and basic motion estimates.
    """

    def __init__(self, static_image_mode: bool = False, model_complexity: int = 1):
        self._mp_pose = mp.solutions.pose
        self._pose = self._mp_pose.Pose(static_image_mode=static_image_mode,
                                        model_complexity=model_complexity)
        self._last_landmarks = None

    def analyze(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Run pose detection on ``frame`` and return landmark info.

        The returned dictionary contains normalized landmark coordinates and
        a rudimentary motion vector (difference from previous frame) when
        available.  ``None`` is returned if no pose was detected.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)
        if not results.pose_landmarks:
            self._last_landmarks = None
            return None

        # convert landmarks to simple dict
        lm = results.pose_landmarks.landmark
        data: Dict[str, Any] = {p.name: (lm[p.value].x, lm[p.value].y, lm[p.value].z)
                                 for p in self._mp_pose.PoseLandmark}

        # compute motion vector if we have previous landmarks
        if self._last_landmarks is not None:
            motions = {}
            for key, coords in data.items():
                prev = self._last_landmarks.get(key)
                if prev is not None:
                    motions[key] = tuple(c - p for c, p in zip(coords, prev))
            data["motions"] = motions
        else:
            data["motions"] = {}

        self._last_landmarks = data
        return data
