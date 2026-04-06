"""Utility for detecting head orientation / attention using MediaPipe FaceMesh."""
from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np
import mediapipe as mp

logger = logging.getLogger(__name__)


class AttentionDetector:
    """Analyzes face landmarks to determine if the person is focused or distracted.

    A simple heuristic uses the position of the nose tip relative to the eye
    centers: if the nose is nearly centered between the eyes, we assume the
    subject is looking forward ("Focused").  Large deviations indicate a
    averted gaze ("Distracted").
    """

    FOCUSED = "Focused"
    DISTRACTED = "Distracted"

    def __init__(self, threshold: float = 0.03):
        # threshold is normalized ratio of deviation allowed
        self.threshold = threshold
        self._mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

    def analyze(self, image: np.ndarray, box: Tuple[int, int, int, int]) -> str:
        """Return attention status for the face inside the given bounding box.

        Args:
            image: BGR frame
            box: (x1, y1, x2, y2) face rectangle in pixel coords
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = box
        # clip and expand a little
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        face_img = image[y1:y2, x1:x2]
        if face_img.size == 0:
            return self.DISTRACTED

        rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        results = self._mesh.process(rgb)
        if not results.multi_face_landmarks:
            return self.DISTRACTED

        lm = results.multi_face_landmarks[0].landmark
        # choose landmarks: nose tip (1), left eye outer (33), right eye outer (263)
        nose = np.array([lm[1].x, lm[1].y])
        left_eye = np.array([lm[33].x, lm[33].y])
        right_eye = np.array([lm[263].x, lm[263].y])

        eye_center = (left_eye + right_eye) / 2.0
        deviation = np.linalg.norm(nose - eye_center)
        if deviation < self.threshold:
            return self.FOCUSED
        else:
            return self.DISTRACTED

    def close(self) -> None:
        try:
            self._mesh.close()
        except Exception:
            pass
