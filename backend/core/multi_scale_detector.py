"""Multi-scale face detector using MTCNN to capture small/distant faces."""
from __future__ import annotations

from typing import List, Tuple
import cv2
import numpy as np

try:
    from mtcnn import MTCNN
except ImportError:
    MTCNN = None  # type: ignore


class MultiScaleDetector:
    def __init__(self, min_face_size: int = 20):
        if MTCNN is None:
            raise RuntimeError("MTCNN library is required for distance recognition")
        self.detector = MTCNN(min_face_size=min_face_size)

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Return list of bounding boxes (x1,y1,x2,y2) for faces in the frame.

        Runs detector on original frame and on an upscaled version to catch
        small faces, then merges results.
        """
        h, w = frame.shape[:2]
        boxes: List[Tuple[int, int, int, int]] = []

        def _scale_boxes(raw_boxes, scale):
            scaled = []
            for b in raw_boxes:
                x, y, bw, bh = b['box']
                x1 = int(x / scale)
                y1 = int(y / scale)
                x2 = int((x + bw) / scale)
                y2 = int((y + bh) / scale)
                scaled.append((x1, y1, x2, y2))
            return scaled

        # original
        results = self.detector.detect_faces(frame)
        boxes.extend(_scale_boxes(results, 1.0))

        # upscale to 2x for small faces
        up = cv2.resize(frame, (w * 2, h * 2))
        results2 = self.detector.detect_faces(up)
        boxes.extend(_scale_boxes(results2, 2.0))

        # filter duplicates by IoU
        final: List[Tuple[int, int, int, int]] = []
        for b in boxes:
            if not any(self._iou(b, f) > 0.5 for f in final):
                final.append(b)
        return final

    @staticmethod
    def _iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
        xA = max(a[0], b[0])
        yA = max(a[1], b[1])
        xB = min(a[2], b[2])
        yB = min(a[3], b[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH
        boxAA = (a[2] - a[0]) * (a[3] - a[1])
        boxBA = (b[2] - b[0]) * (b[3] - b[1])
        if boxAA + boxBA - interArea == 0:
            return 0.0
        return interArea / float(boxAA + boxBA - interArea)
