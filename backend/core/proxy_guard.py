"""Proxy detection and guard module to prevent fake attendance."""
from __future__ import annotations

import csv
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp

from .dataset_loader import DatasetLoader
from .embedding_validator import EmbeddingValidator
from .liveness_detector import LivenessDetector

logger = logging.getLogger(__name__)


class ProxyGuard:
    def __init__(
        self,
        dataset_path: Path | str = None,
        similarity_threshold: float = 0.6,
        frame_skip: int = 2,
    ):
        # load reference embeddings (all images per student)
        if dataset_path is None:
            dataset_path = Path("dataset")
        loader = DatasetLoader(dataset_path)
        self.reference: Dict[str, List[np.ndarray]] = loader.load_embeddings_multi()
        self.validator = EmbeddingValidator(self.reference, threshold=similarity_threshold)
        self.liveness = LivenessDetector()
        self.frame_counter = 0
        self.frame_skip = frame_skip

        # used for re-verification
        self._last_seen: Dict[int, Tuple[Optional[str], Optional[np.ndarray], float]] = {}

        # prepare log file
        self.log_path = Path("logs/proxy_attempts.csv")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with self.log_path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["student_name", "timestamp", "confidence_score", "reason"])

    def log_attempt(self, name: Optional[str], confidence: float, reason: str) -> None:
        with self.log_path.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name or "Unknown", time.time(), confidence, reason])
        logger.warning("proxy guard: %s (%s) reason=%s", name, confidence, reason)

    def _detect_multi_faces(self, image: np.ndarray, box: Tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = box
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return False
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as detector:
            results = detector.process(rgb)
        if not results.detections:
            return False
        # if more than one detection inside crop
        return len(results.detections) > 1

    def analyze(self, frame: np.ndarray, results: List[Dict]) -> List[Dict]:
        """Augment results with proxy_status and possibly log attempts."""
        self.frame_counter += 1
        enhanced = []
        for res in results:
            status = "valid"
            proxy_reason = None
            name = res.get("name")
            conf = res.get("confidence", 0.0)
            tid = res.get("id")
            emb = res.get("embedding")

            # perform checks only every nth frame
            if self.frame_counter % self.frame_skip == 0:
                # liveness check
                if emb is not None or name:
                    if not self.liveness.check(frame, res.get("box", (0, 0, 0, 0))):
                        status = "proxy"
                        proxy_reason = "NO_BLINK"
                        self.log_attempt(name, conf, proxy_reason)
                # consistency vs stored embeddings
                if status == "valid" and emb is not None and name:
                    good = self.validator.validate(name, emb)
                    if not good:
                        status = "suspicious"
                        proxy_reason = "LOW_CONFIDENCE"
                        self.log_attempt(name, conf, proxy_reason)
                # multi-face in box
                if status == "valid" and self._detect_multi_faces(frame, res.get("box", (0, 0, 0, 0))):
                    status = "proxy"
                    proxy_reason = "MULTIPLE_FACES"
                    self.log_attempt(name, conf, proxy_reason)
                # re-verification of same ID after delay
                prev = self._last_seen.get(tid)
                if prev is not None:
                    prev_name, prev_emb, prev_time = prev
                    if time.time() - prev_time >= 2:
                        # verify that embedding/name match
                        if name != prev_name or (
                            emb is not None
                            and prev_emb is not None
                            and np.linalg.norm(emb - prev_emb) > self.validator.threshold
                        ):
                            status = "proxy"
                            proxy_reason = "FACE_CHANGED"
                            self.log_attempt(name, conf, proxy_reason)
            # update last seen record
            if tid is not None:
                self._last_seen[tid] = (name, emb, time.time())

            res2 = dict(res)
            res2["proxy_status"] = status
            if proxy_reason:
                res2["proxy_reason"] = proxy_reason
            enhanced.append(res2)
        return enhanced

    def close(self) -> None:
        try:
            self.liveness.close()
        except Exception:
            pass
