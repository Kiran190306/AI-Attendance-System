from __future__ import annotations

import threading
import logging
from datetime import datetime
from typing import Any, Dict

import cv2

from . import utils
from . import config
from .recognition_engine import SharedRecognitionEngine
from .tracker import Tracker
from .events.event_bus import EventBus

# crowd analytics
from .analytics.crowd_analyzer import CrowdAnalyzer
from .behavior.behavior_detector import BehaviorDetector


logger = logging.getLogger(__name__)


class StreamProcessor(threading.Thread):
    """Thread that captures frames from a single camera and runs detection.

    Results are overlaid onto the frame and pushed to an event bus.  The
    ``last_display`` attribute always holds the most recent annotated frame so
    that the display thread in :class:`CameraManager` can compose a grid.
    """

    def __init__(
        self,
        camera_id: str,
        source: Any,
        engine: SharedRecognitionEngine,
        tracker: Tracker,
        event_bus: EventBus,
    ) -> None:
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.source = source
        self.engine = engine
        self.tracker = tracker
        self.bus = event_bus
        self.cap: cv2.VideoCapture | None = None
        self.running = False
        self.last_display = None
        # behavior detector (shared per stream)
        self.behavior = BehaviorDetector()

    def run(self) -> None:
        logger.info("starting stream processor for %s (%s)", self.camera_id, self.source)
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logger.error("unable to open source for %s", self.camera_id)
            return
        self.running = True

        # lazy instantiation of crowd analyzer for this stream
        self.crowd: CrowdAnalyzer | None = None

        while self.running:
            ret, frame = self.cap.read()
            # log arrival of frame (camera event)
            try:
                with open("logs/camera_events.log", "a", encoding="utf-8") as _f:
                    _f.write(f"{datetime.now().isoformat()} {self.camera_id} frame\n")
            except Exception:
                pass

            if not ret or frame is None:
                logger.warning("empty frame from %s, terminating thread", self.camera_id)
                break

            # initialize analyzer once we have a frame
            if self.crowd is None:
                self.crowd = CrowdAnalyzer(frame_skip=3, target_width=640)

            results, display_frame = self.engine.process_frame(frame)

            # perform crowd analytics on this frame
            crowd_info = self.crowd.analyze(frame, self.camera_id)
            if crowd_info:
                info_lines = [
                    f"People: {crowd_info['count']}",
                    f"Density: {crowd_info['density']}"
                ]
                utils.draw_info_panel(
                    display_frame,
                    "CROWD",
                    info_lines,
                    position="bottom-right",
                    bg_color=(80, 30, 30),
                )
                heat = crowd_info.get("heatmap_overlay")
                if heat is not None:
                    display_frame = cv2.addWeighted(display_frame, 0.7, heat, 0.3, 0)

                # publish crowd event
                self.bus.publish({
                    "type": "crowd",
                    "camera_id": self.camera_id,
                    "count": crowd_info["count"],
                    "density": crowd_info["density"],
                    "timestamp": datetime.now().isoformat(),
                })

            # annotate and publish events
            now_iso = datetime.now().isoformat()
            for face in results:
                name = face.get("name")
                conf = face.get("confidence", 0.0)
                track_id = None
                if name:
                    track_id = self.tracker.assign(name)

                # behavior analysis for this person
                behavior_label, behavior_conf = self.behavior.process(
                    display_frame, track_id, face.get("box"),
                )

                # choose overlay color based on behavior
                if behavior_label == "AGGRESSIVE":
                    color = (0, 0, 255)
                elif behavior_label == "SUSPICIOUS":
                    color = (0, 255, 255)
                else:
                    color = (0, 255, 0) if name else (0, 0, 255)

                # overlay text includes behavior
                parts = [self.camera_id]
                if name:
                    parts.append(name)
                else:
                    parts.append("Unknown")
                if track_id is not None:
                    parts.append(f"ID:{track_id}")
                parts.append(behavior_label)
                label = " | ".join(parts)

                x1, y1, x2, y2 = face["box"]
                utils.draw_box_with_label(display_frame, x1, y1, x2, y2, label, color, thickness=2)

                # log behavior if not normal
                if behavior_label != "NORMAL":
                    try:
                        with open(config.BEHAVIOR_LOG_CSV, "a", newline="", encoding="utf-8") as bf:
                            bf.write(f"{self.camera_id},{now_iso},{track_id},{behavior_label},{behavior_conf:.2f}\n")
                    except Exception:
                        pass

                # push event for attendance
                event: Dict[str, Any] = {
                    "camera_id": self.camera_id,
                    "student_name": name,
                    "confidence": conf,
                    "timestamp": now_iso,
                }
                self.bus.publish(event)

            # store display frame for compositor
            self.last_display = display_frame

        if self.cap:
            self.cap.release()
        logger.info("stopping stream processor for %s", self.camera_id)

    def stop(self) -> None:
        self.running = False
