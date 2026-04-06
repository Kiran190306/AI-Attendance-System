"""Simple liveness / anti-spoof detector using MediaPipe FaceMesh.

Features:
- eye blink detection via eye aspect ratio (EAR)
- head movement detection (nose position drift)

API:
    detector = LivenessDetector()
    live = detector.check(frame, box)

"""
from __future__ import annotations

import logging
from typing import Tuple, Optional

import cv2
import numpy as np
import mediapipe as mp

logger = logging.getLogger(__name__)


class LivenessDetectorError(Exception):
    pass


class LivenessDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        # lightweight model
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False,
                                                   max_num_faces=1,
                                                   refine_landmarks=True,
                                                   min_detection_confidence=0.5,
                                                   min_tracking_confidence=0.5)
        self.prev_nose: Optional[Tuple[float,float]] = None
        self.blink_threshold = 0.2  # empiric
        self.movement_threshold = 5  # pixels

    def _eye_aspect_ratio(self, landmarks, left_indices, right_indices, image_shape):
        h, w = image_shape[:2]
        def ear(pts):
            # compute distances between vertical and horizontal eye landmarks
            a = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
            b = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
            c = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
            if c == 0:
                return 0.0
            return (a + b) / (2.0 * c)

        lpts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in left_indices]
        rpts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in right_indices]
        return ear(lpts), ear(rpts)

    def _has_moved(self, nose_point: Tuple[int,int]) -> bool:
        if self.prev_nose is None:
            self.prev_nose = nose_point
            return False
        dx = abs(nose_point[0] - self.prev_nose[0])
        dy = abs(nose_point[1] - self.prev_nose[1])
        moved = dx > self.movement_threshold or dy > self.movement_threshold
        if moved:
            self.prev_nose = nose_point
        return moved

    def check(self, frame: np.ndarray, box: Tuple[int,int,int,int]) -> bool:
        """Return True if liveness confirmed for given face box."""
        x1,y1,x2,y2 = box
        face = frame[y1:y2, x1:x2]
        if face.size == 0:
            return False
        rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return False
        landmarks = results.multi_face_landmarks[0].landmark
        # eye landmarks from MediaPipe
        left_idxs = [33, 160, 158, 133, 153, 144]
        right_idxs = [263, 387, 385, 362, 380, 373]
        left_ear, right_ear = self._eye_aspect_ratio(landmarks, left_idxs, right_idxs, face.shape)
        ear = (left_ear + right_ear) / 2.0
        blink = ear < self.blink_threshold
        # nose index
        nose = landmarks[1]
        h,w = face.shape[:2]
        nose_point = (int(nose.x * w) + x1, int(nose.y * h) + y1)
        moved = self._has_moved(nose_point)
        live = blink or moved
        if not live:
            logger.debug("liveness check failed (EAR=%.3f blink=%s moved=%s)", ear, blink, moved)
        return live

    def close(self):
        self.face_mesh.close()
