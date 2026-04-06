import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from collections import deque

import cv2
import numpy as np
import mediapipe as mp

from .tracker import PersonTracker
from .liveness_detector import LivenessDetector
from .presence_analyzer import SmartPresenceAnalyzer

try:
    import face_recognition
except ImportError:
    face_recognition = None  # type: ignore

from .. import config
from .dataset_loader import DatasetLoader, DatasetLoaderError

logger = logging.getLogger(__name__)


class FaceRecognitionEngineError(Exception):
    pass


class FaceRecognitionEngine:
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

        self._name_list: List[str] = []
        self._emb_array: Optional[np.ndarray] = None
        self._detector: Optional[mp.solutions.face_detection.FaceDetection] = None
        self._frame_counter = 0

        self._frame_times = deque(maxlen=30)
        self._detection_times = deque(maxlen=30)
        self._recognition_times = deque(maxlen=30)

        # advanced features
        self.tracker = PersonTracker()
        self.liveness = LivenessDetector()
        # presence intelligence
        self.presence = SmartPresenceAnalyzer()

    def initialize(self) -> None:
        loader = DatasetLoader(self.dataset_path)
        try:
            embeddings = loader.load_embeddings()
        except DatasetLoaderError as exc:
            raise FaceRecognitionEngineError(exc)

        if not embeddings:
            raise FaceRecognitionEngineError("no embeddings available after dataset scan")

        self._name_list = list(embeddings.keys())
        self._emb_array = np.vstack([embeddings[n] for n in self._name_list])

        mp_face = mp.solutions.face_detection
        self._detector = mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=self.detection_confidence,
        )
        logger.info("face engine initialized with %d students", len(self._name_list))

    def close(self) -> None:
        if self._detector:
            self._detector.close()
            self._detector = None
        if hasattr(self, 'liveness') and self.liveness is not None:
            try:
                self.liveness.close()
            except Exception:
                pass
        if hasattr(self, 'presence') and self.presence is not None:
            try:
                self.presence.close()
            except Exception:
                pass

    def get_performance_stats(self) -> Dict:
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

    def _detect_boxes(self, frame: np.ndarray, scale_factor: float = 1.0) -> List[Tuple[int, int, int, int]]:
        assert self._detector is not None, "engine not initialized"
        h, w = frame.shape[:2]
        if self.detection_scale < 1.0:
            small = cv2.resize(
                frame,
                (int(w * self.detection_scale), int(h * self.detection_scale)),
                interpolation=cv2.INTER_LINEAR,
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
        if self._emb_array is None:
            return None
        top, right, bottom, left = box[1], box[2], box[3], box[0]
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encs = face_recognition.face_encodings(rgb, [(top, right, bottom, left)])
            if encs:
                return np.array(encs[0], dtype=np.float32)
        except Exception as exc:
            logger.debug("embedding extraction failed: %s", exc)
        return None

    def _recognize(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        if self._emb_array is None or len(self._emb_array) == 0:
            return None, 0.0
        distances = np.linalg.norm(self._emb_array - embedding, axis=1)
        idx = int(np.argmin(distances))
        dist = float(distances[idx])
        if dist > self.match_threshold:
            return None, 0.0
        confidence = max(0.0, 1.0 - dist / self.match_threshold)
        if confidence < self.recognition_confidence:
            return None, 0.0
        return self._name_list[idx], confidence

    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        frame_start = time.time()
        self._frame_counter += 1
        h, w = frame.shape[:2]
        if w > self.target_frame_width:
            aspect = h / w
            new_h = int(self.target_frame_width * aspect)
            frame_display = cv2.resize(
                frame,
                (self.target_frame_width, new_h),
                interpolation=cv2.INTER_LINEAR,
            )
            scale_factor = w / self.target_frame_width
        else:
            frame_display = frame
            scale_factor = 1.0

        if self._frame_counter % self.frame_skip != 0:
            self._frame_times.append(time.time() - frame_start)
            return [], frame_display

        detect_start = time.time()
        boxes = self._detect_boxes(frame_display, scale_factor)
        self._detection_times.append(time.time() - detect_start)

        recog_start = time.time()
        results: List[Dict] = []

        # update trackers with current detections
        tracked = self.tracker.update(frame_display, boxes)
        for tid, info in tracked.items():
            box = info["box"]
            # perform recognition/liveness once per tracked person
            if not info.get("recognized"):
                emb = self._extract_embedding(frame_display, box)
                if emb is not None:
                    name, conf = self._recognize(emb)
                    if name:
                        live = self.liveness.check(frame_display, box)
                        if live:
                            info["name"] = name
                            info["confidence"] = conf
                            info["recognized"] = True
                            info["emb"] = emb
                            logger.info("recognized %s (id=%d)", name, tid)
                        else:
                            info["name"] = "Spoof Detected"
                            info["confidence"] = 0.0
                            logger.warning("spoof attempt id=%d", tid)
                    else:
                        info["name"] = None
                        info["confidence"] = 0.0
            results.append({
                "id": tid,
                "box": box,
                "name": info.get("name"),
                "confidence": info.get("confidence", 0.0),
                "embedding": info.get("emb"),
            })
        self._recognition_times.append(time.time() - recog_start)

        # run presence analysis if available
        if hasattr(self, "presence") and self.presence is not None:
            try:
                results = self.presence.update(frame_display, results)
            except Exception as e:
                logger.debug("presence analysis error: %s", e)
        self._frame_times.append(time.time() - frame_start)
        return results, frame_display
