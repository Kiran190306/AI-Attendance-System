"""Simple eye blink detector using landmark-based eye aspect ratio."""
from __future__ import annotations

import logging
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)


# indices for MediaPipe FaceMesh landmarks corresponding to eye
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]


def _eye_aspect_ratio(landmarks: np.ndarray) -> float:
    # landmarks is an array of shape (468, 3) normalized
    # compute EAR for one eye using six points
    # p1-p6 order if passed appropriately
    # formula: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    A = np.linalg.norm(landmarks[1] - landmarks[5])
    B = np.linalg.norm(landmarks[2] - landmarks[4])
    C = np.linalg.norm(landmarks[0] - landmarks[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)


class BlinkDetector:
    """Keeps track of blink count and sleeping status per face.

    A blink is detected when the eye aspect ratio falls below a threshold and
    then rises again.  Sleeping is simply prolonged closure beyond a frame
    count threshold.
    """

    def __init__(
        self,
        ear_threshold: float = 0.2,
        consec_frames: int = 2,
        sleep_frames: int = 30,
    ):
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.sleep_frames = sleep_frames
        self.frame_counter = 0
        self.blink_count = 0
        self.closed_frames = 0

    def update(self, landmarks: np.ndarray) -> Tuple[int, bool]:
        """Update with new landmarks and return (total_blinks, sleeping_flag)."""
        if landmarks is None or landmarks.shape[0] == 0:
            return self.blink_count, False

        # compute EAR for both eyes
        left = landmarks[LEFT_EYE_IDX]
        right = landmarks[RIGHT_EYE_IDX]
        ear_l = _eye_aspect_ratio(left)
        ear_r = _eye_aspect_ratio(right)
        ear = (ear_l + ear_r) / 2.0
        self.frame_counter += 1
        sleeping = False

        if ear < self.ear_threshold:
            self.closed_frames += 1
            if self.closed_frames >= self.sleep_frames:
                sleeping = True
        else:
            if self.closed_frames >= self.consec_frames:
                self.blink_count += 1
            self.closed_frames = 0
        return self.blink_count, sleeping

    def reset(self) -> None:
        self.frame_counter = 0
        self.blink_count = 0
        self.closed_frames = 0
