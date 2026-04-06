"""Engine optimized for long-distance / small-face recognition."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import cv2
import numpy as np

from .multi_scale_detector import MultiScaleDetector
from .face_enhancer import enhance_face
from .tracker import PersonTracker

try:
    import face_recognition
except ImportError:
    face_recognition = None  # type: ignore

from .. import config
from .dataset_loader import DatasetLoader, DatasetLoaderError

logger = logging.getLogger(__name__)


class DistanceRecognitionEngineError(Exception):
    pass


class DistanceRecognitionEngine:
    def __init__(
        self,
        dataset_path: Path | str = config.DATASET_PATH,
        detection_scale: float = 1.0,
        frame_skip: int = 2,
        match_threshold: float = config.EMBEDDING_DISTANCE_THRESHOLD,
        recognition_confidence: float = config.MIN_RECOGNITION_CONFIDENCE,
        target_frame_width: int = 1280,
    ):
        if face_recognition is None:
            raise RuntimeError("face_recognition library required")
        self.dataset_path = Path(dataset_path)
        self.match_threshold = match_threshold
        self.recognition_confidence = recognition_confidence
        self.target_frame_width = target_frame_width
        self.frame_skip = frame_skip

        self._name_list: List[str] = []
        self._emb_array: Optional[np.ndarray] = None
        self._detector: Optional[MultiScaleDetector] = None
        self._frame_counter = 0

        self._frame_times = []
        self._detection_times = []
        self._recognition_times = []

        # tracking for distant faces
        self.tracker = PersonTracker()

    def initialize(self) -> None:
        loader = DatasetLoader(self.dataset_path)
        try:
            embeddings = loader.load_embeddings()
        except DatasetLoaderError as exc:
            raise DistanceRecognitionEngineError(exc)
        if not embeddings:
            raise DistanceRecognitionEngineError("no embeddings available")
        self._name_list = list(embeddings.keys())
        self._emb_array = np.vstack([embeddings[n] for n in self._name_list])
        self._detector = MultiScaleDetector()
        logger.info("distance engine initialized with %d students", len(self._name_list))

    def get_student_list(self) -> List[str]:
        return list(self._name_list)

    def close(self) -> None:
        # nothing special
        pass

    def _detect_boxes(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        assert self._detector is not None
        return self._detector.detect(frame)

    def _extract_embedding(self, face: np.ndarray) -> Optional[np.ndarray]:
        if self._emb_array is None:
            return None
        try:
            rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb)
            if encs:
                return np.array(encs[0], dtype=np.float32)
        except Exception as exc:
            logger.debug("dist emb extract failed: %s", exc)
        return None

    def _recognize(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        if self._emb_array is None or len(self._emb_array) == 0:
            return None, 0.0
        distances = np.linalg.norm(self._emb_array - embedding, axis=1)
        idx = int(np.argmin(distances))
        dist = float(distances[idx])
        # adaptive threshold: smaller faces allowed looser threshold
        # not implemented fully; just use base
        if dist > self.match_threshold:
            return None, 0.0
        confidence = max(0.0, 1.0 - dist / self.match_threshold)
        if confidence < self.recognition_confidence:
            return None, 0.0
        return self._name_list[idx], confidence

    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Detect and recognize in long-distance scenario."""
        frame_start = time.time()
        self._frame_counter += 1
        h, w = frame.shape[:2]
        # resize for performance
        if w > self.target_frame_width:
            aspect = h / w
            new_h = int(self.target_frame_width * aspect)
            frame_display = cv2.resize(frame, (self.target_frame_width, new_h))
        else:
            frame_display = frame

        if self._frame_counter % self.frame_skip != 0:
            return [], frame_display

        detect_start = time.time()
        boxes = self._detect_boxes(frame_display)
        self._detection_times.append(time.time() - detect_start)

        results = []
        recog_start = time.time()
        tracked = self.tracker.update(frame_display, boxes)
        for tid, info in tracked.items():
            box = info['box']
            if not info.get('recognized'):
                # enhance small face
                x1, y1, x2, y2 = box
                face = frame_display[y1:y2, x1:x2]
                if face.size == 0:
                    continue
                if max(face.shape[:2]) < 80:
                    face = enhance_face(face)
                emb = self._extract_embedding(face)
                if emb is not None:
                    name, conf = self._recognize(emb)
                    if name:
                        info['name'] = name
                        info['confidence'] = conf
                        info['recognized'] = True
                        info['embedding'] = emb
                        logger.info("distance recognized %s (id=%d)", name, tid)
                    else:
                        info['name'] = None
                        info['confidence'] = 0.0
            # compute distance estimate (heuristic)
            x1, y1, x2, y2 = box
            fh = y2 - y1
            dist_est = None
            if fh > 0:
                # simple inverse relation, scale factor 500
                dist_est = 500.0 / fh
            results.append({
                'id': tid,
                'box': box,
                'name': info.get('name'),
                'confidence': info.get('confidence',0.0),
                'embedding': info.get('embedding'),
                'distance': dist_est,
            })
        self._recognition_times.append(time.time() - recog_start)
        self._frame_times.append(time.time() - frame_start)
        return results, frame_display

    def get_performance_stats(self) -> Dict:
        avg_frame = np.mean(self._frame_times) if self._frame_times else 0
        fps = 1.0 / avg_frame if avg_frame > 0 else 0
        return {
            'fps': round(fps,1),
            'avg_frame_time_ms': round(avg_frame*1000,2)
        }
