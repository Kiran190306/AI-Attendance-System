from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from collections import deque
import time

import cv2
import numpy as np
import mediapipe as mp

try:
    import face_recognition
except ImportError:
    face_recognition = None  # type: ignore

from . import config
from .dataset_loader import DatasetLoader, DatasetLoaderError

logger = logging.getLogger(__name__)


class FaceRecognitionEngineError(Exception):
    pass


class FaceRecognitionEngine:
    """Encapsulates face detection + recognition logic for the attendance system.

    The class is intentionally lightweight and does *not* hold state about
    marked attendance; that's the responsibility of :class:`AttendanceService`.

    Usage::

        engine = FaceRecognitionEngine()
        engine.initialize()                # load dataset, prepare detector

        result = engine.process_frame(frame)
        for face in result:
            name = face['name']            # None for unknown
            box = face['box']              # (x1,y1,x2,y2)
            confidence = face['confidence']
    """

    def __init__(
        self,
        dataset_path: Path | str = config.DATASET_PATH,
        detection_confidence: float = config.MIN_DETECTION_CONFIDENCE,
        detection_scale: float = config.DETECTION_SCALE,
        frame_skip: int = config.FRAME_SKIP,
        match_threshold: float = config.EMBEDDING_DISTANCE_THRESHOLD,
        recognition_confidence: float = config.MIN_RECOGNITION_CONFIDENCE,
        target_frame_width: int = 640,
    ):
        self.dataset_path = Path(dataset_path)
        self.detection_confidence = detection_confidence
        self.detection_scale = detection_scale
        self.frame_skip = frame_skip
        self.match_threshold = match_threshold
        self.recognition_confidence = recognition_confidence
        self.target_frame_width = target_frame_width

        # populated during initialize()
        self._name_list: List[str] = []
        self._emb_array: Optional[np.ndarray] = None
        self._detector: Optional[mp.solutions.face_detection.FaceDetection] = None

        # frame counter (for skipping)
        self._frame_counter = 0
        
        # performance metrics
        self._frame_times = deque(maxlen=30)
        self._detection_times = deque(maxlen=30)
        self._recognition_times = deque(maxlen=30)

    # ------------------------------------------------------------------
    # setup / initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Load student embeddings and create the Mediapipe detector."""
        loader = DatasetLoader(self.dataset_path)
        try:
            embeddings = loader.load_embeddings()
        except DatasetLoaderError as exc:
            raise FaceRecognitionEngineError(exc)

        if not embeddings:
            raise FaceRecognitionEngineError("no embeddings available after dataset scan")

        # prepare internal structures for fast recognition
        self._name_list = list(embeddings.keys())
        self._emb_array = np.vstack([embeddings[n] for n in self._name_list])

        mp_face = mp.solutions.face_detection
        self._detector = mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=self.detection_confidence,
        )
        logger.info("face engine initialized with %d students", len(self._name_list))

    def close(self) -> None:
        """Release any resources held by the engine."""
        if self._detector:
            self._detector.close()
            self._detector = None

    def get_performance_stats(self) -> Dict:
        """Return performance metrics for the last ~30 frames."""
        avg_frame_time = np.mean(self._frame_times) if self._frame_times else 0
        avg_detect_time = np.mean(self._detection_times) if self._detection_times else 0
        avg_recog_time = np.mean(self._recognition_times) if self._recognition_times else 0
        
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        return {
            "fps": round(fps, 1),
            "avg_frame_time_ms": round(avg_frame_time * 1000, 2),
            "avg_detection_time_ms": round(avg_detect_time * 1000, 2),
            "avg_recognition_time_ms": round(avg_recog_time * 1000, 2),
            "frame_skip": self.frame_skip,
            "target_frame_width": self.target_frame_width,
            "enrolled_students": len(self._name_list),
        }

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _detect_boxes(self, frame: np.ndarray, scale_factor: float = 1.0) -> List[Tuple[int, int, int, int]]:
        """Run Mediapipe detection on resized frame, return boxes scaled to frame coords.
        
        Args:
            frame: Input frame (already resized to target size)
            scale_factor: How much the original frame was scaled down
        """
        assert self._detector is not None, "engine not initialized"

        h, w = frame.shape[:2]
        
        # Apply detection scale for additional speed (downsampling for detection)
        if self.detection_scale < 1.0:
            small = cv2.resize(
                frame, 
                (int(w * self.detection_scale), int(h * self.detection_scale)),
                interpolation=cv2.INTER_LINEAR
            )
        else:
            small = frame

        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self._detector.process(rgb)
        boxes: list[Tuple[int, int, int, int]] = []

        if results.detections:
            scale = self.detection_scale or 1.0
            for det in results.detections:
                bbox = det.location_data.relative_bounding_box
                x1 = max(0, int(bbox.xmin * w / scale))
                y1 = max(0, int(bbox.ymin * h / scale))
                x2 = min(w, int((bbox.xmin + bbox.width) * w / scale))
                y2 = min(h, int((bbox.ymin + bbox.height) * h / scale))
                boxes.append((x1, y1, x2, y2))
        return boxes

    def _extract_embedding(
        self, frame: np.ndarray, box: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """Crop face region and return 128‑d embedding or ``None``."""
        if self._emb_array is None:
            return None
        top, right, bottom, left = box[1], box[2], box[3], box[0]
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb, [(top, right, bottom, left)])
            if encs:
                return np.array(encs[0], dtype=np.float32)
        except Exception as exc:  # pragma: no cover - fallback
            logger.debug("embedding extraction failed: %s", exc)
        return None

    def _recognize(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """Return (name, confidence) or (None,0.0)."""
        if self._emb_array is None or len(self._emb_array) == 0:
            return None, 0.0

        # vectorized distance
        distances = np.linalg.norm(self._emb_array - embedding, axis=1)
        idx = int(np.argmin(distances))
        dist = float(distances[idx])
        if dist > self.match_threshold:
            return None, 0.0
        confidence = max(0.0, 1.0 - dist / self.match_threshold)
        if confidence < self.recognition_confidence:
            return None, 0.0
        return self._name_list[idx], confidence

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Analyze one frame optimized for real-time performance.
        
        Resizes frame early, skips detection on most frames, returns both results
        and display frame for efficient rendering.
        
        Each result dict has keys: ``box`` (x1,y1,x2,y2), ``name`` (None for unknown),
        ``confidence`` (float 0‑1).
        
        Returns:
            (results_list, display_frame) - display frame is resized for efficiency
        """
        frame_start = time.time()
        self._frame_counter += 1

        # Resize frame ONCE at start for all processing (early in pipeline)
        h, w = frame.shape[:2]
        if w > self.target_frame_width:
            aspect = h / w
            new_h = int(self.target_frame_width * aspect)
            frame_display = cv2.resize(
                frame,
                (self.target_frame_width, new_h),
                interpolation=cv2.INTER_LINEAR
            )
            scale_factor = w / self.target_frame_width
        else:
            frame_display = frame
            scale_factor = 1.0

        # Skip detection on most frames for speed
        if self._frame_counter % self.frame_skip != 0:
            self._frame_times.append(time.time() - frame_start)
            return [], frame_display

        # Detect faces (on downsampled frame if needed)
        detect_start = time.time()
        boxes = self._detect_boxes(frame_display, scale_factor)
        self._detection_times.append(time.time() - detect_start)

        # Recognize each detected face
        recog_start = time.time()
        results: List[Dict] = []
        for box in boxes:
            emb = self._extract_embedding(frame_display, box)
            if emb is None:
                results.append({"box": box, "name": None, "confidence": 0.0})
                continue
            name, conf = self._recognize(emb)
            results.append({"box": box, "name": name, "confidence": conf})
        self._recognition_times.append(time.time() - recog_start)

        # Track frame time
        self._frame_times.append(time.time() - frame_start)
        return results, frame_display
