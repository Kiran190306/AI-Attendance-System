"""Smart presence analysis combining attention, blink and tracking metrics."""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np

from .tracker import PersonTracker
from .attention_detector import AttentionDetector
from .blink_detector import BlinkDetector
from ..analytics.session_logger import SessionLogger

logger = logging.getLogger(__name__)


class PresenceRecord:
    def __init__(self, name: Optional[str], tid: int):
        self.name = name
        self.tid = tid
        self.start_time = time.time()
        self.last_time = self.start_time
        self.presence_time = 0.0
        self.focus_frames = 0
        self.distracted_frames = 0
        self.blink_count = 0
        self.status = ""  # Focused/ Distracted/ Sleeping

    def update_time(self) -> None:
        now = time.time()
        self.presence_time += now - self.last_time
        self.last_time = now

    def metrics(self) -> Dict:
        total = self.focus_frames + self.distracted_frames
        focus_pct = 0.0
        distraction_pct = 0.0
        if total > 0:
            focus_pct = self.focus_frames / total * 100.0
            distraction_pct = self.distracted_frames / total * 100.0
        return {
            "name": self.name or "Unknown",
            "time_present": round(self.presence_time, 2),
            "focus_percent": round(focus_pct, 1),
            "distraction_percent": round(distraction_pct, 1),
            "blink_count": self.blink_count,
        }


class SmartPresenceAnalyzer:
    """Tracks presence, attention and blinking for each recognized person."""

    def __init__(self, logger_obj: Optional[SessionLogger] = None):
        self.tracker = PersonTracker()
        self.attention = AttentionDetector()
        self.blink = BlinkDetector()
        self.records: Dict[int, PresenceRecord] = {}
        self.frame_counter = 0
        self.session_logger = logger_obj or SessionLogger()

    def update(self, frame: np.ndarray, results: List[Dict]) -> List[Dict]:
        """Call once per frame after recognition/tracking results available.

        Returns a list of augmented result dictionaries.
        """
        self.frame_counter += 1
        h, w = frame.shape[:2]

        # update each record, compute attention/blink
        enhanced = []
        for res in results:
            tid = res.get("id")
            box = res.get("box")
            name = res.get("name")
            # maintain record entry
            if tid not in self.records:
                self.records[tid] = PresenceRecord(name, tid)
            rec = self.records[tid]
            rec.name = name or rec.name
            rec.update_time()

            status = ""
            blink_cnt = 0
            # only analyze attention/blink every second frame to save CPU
            if box and (self.frame_counter % 2 == 0):
                # run attention detector
                try:
                    status = self.attention.analyze(frame, box)
                except Exception as e:
                    logger.debug("attention analysis failed: %s", e)
                    status = AttentionDetector.DISTRACTED
                # run blink detector by getting full mesh landmarks first
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # run a full face mesh pass
                    mp_mesh = self.attention._mesh
                    mesh_result = mp_mesh.process(rgb)
                    landmarks = None
                    if mesh_result.multi_face_landmarks:
                        lm = mesh_result.multi_face_landmarks[0].landmark
                        # convert to numpy array
                        landmarks = np.array([[p.x, p.y, p.z] for p in lm])
                    blink_cnt, sleeping = self.blink.update(landmarks)
                    if sleeping:
                        status = "Sleeping"
                except Exception as e:
                    logger.debug("blink analysis failed: %s", e)
            # update record counters
            if status == AttentionDetector.FOCUSED:
                rec.focus_frames += 1
            elif status == AttentionDetector.DISTRACTED:
                rec.distracted_frames += 1
            elif status == "Sleeping":
                # treat sleeping as distracted but flag specially
                rec.distracted_frames += 1
            rec.blink_count = blink_cnt
            rec.status = status

            enhanced.append({
                **res,
                "status": status,
                "presence_time": rec.presence_time,
            })
        return enhanced

    def session_metrics(self) -> List[Dict]:
        """Return metrics for all records; also log them to csv."""
        metrics = []
        for rec in self.records.values():
            m = rec.metrics()
            metrics.append(m)
            self.session_logger.log(m)
        return metrics

    def close(self) -> None:
        # log remaining data
        try:
            self.session_metrics()
        except Exception:
            pass
        try:
            self.attention.close()
        except Exception:
            pass
