
"""Simple person tracker using OpenCV tracker objects.

Tracks bounding boxes across frames and assigns each a unique ID.  Recognition
is performed only when a new tracker is created (i.e. new face).  Prevents
repeated recognition of already-tracked persons.
"""
from __future__ import annotations

import cv2
import logging
import numpy as np
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


def _create_tracker(kind: str = "CSRT") -> cv2.Tracker:
    if kind.upper() == "CSRT":
        return cv2.TrackerCSRT_create()
    else:
        return cv2.TrackerKCF_create()


def _iou(boxA: Tuple[int,int,int,int], boxB: Tuple[int,int,int,int]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    if boxAArea + boxBArea - interArea == 0:
        return 0.0
    return interArea / float(boxAArea + boxBArea - interArea)


class PersonTracker:
    def __init__(self, tracker_type: str = "CSRT", iou_threshold: float = 0.5):
        self.tracker_type = tracker_type
        self.iou_threshold = iou_threshold
        self.trackers: Dict[int, cv2.Tracker] = {}
        self.data: Dict[int, Dict] = {}
        self.next_id = 1

    def update(self, frame, detections: list[Tuple[int,int,int,int]]):
        # update existing trackers
        remove_ids = []
        for tid, tr in list(self.trackers.items()):
            ok, bbox = tr.update(frame)
            if not ok:
                remove_ids.append(tid)
            else:
                x, y, w, h = [int(v) for v in bbox]
                self.data[tid]["box"] = (x, y, x+w, y+h)
        for rid in remove_ids:
            logger.debug("removing tracker %d", rid)
            del self.trackers[rid]
            del self.data[rid]

        # add new trackers for unmatched detections
        for box in detections:
            matched = False
            for tid, info in self.data.items():
                if _iou(info["box"], box) > self.iou_threshold:
                    matched = True
                    break
            if not matched:
                tid = self.next_id
                self.next_id += 1
                tr = _create_tracker(self.tracker_type)
                x1,y1,x2,y2 = box
                w = x2 - x1
                h = y2 - y1
                tr.init(frame, (x1, y1, w, h))
                self.trackers[tid] = tr
                self.data[tid] = {"box": box, "recognized": False, "name": None, "confidence": 0.0}
                logger.debug("created new tracker %d for box %s", tid, box)
        return self.data
