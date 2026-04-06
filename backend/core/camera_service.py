"""Camera service for real-time face recognition and attendance tracking."""
import logging
import cv2
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List

from .face_engine import FaceRecognitionEngine
from .attention_detector import AttentionDetector
from .proxy_guard import ProxyGuard

logger = logging.getLogger(__name__)


class CameraServiceError(Exception):
    pass


class CameraService:
    def __init__(
        self,
        face_engine: FaceRecognitionEngine,
        camera_id: int = 0,
        target_fps: int = 15,
        presence_analyzer=None,
    ):
        self.face_engine = face_engine
        self.camera_id = camera_id
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._session_data = {
            "marked_today": {},
            "frame_count": 0,
            "unknown_faces": 0,
            "start_time": None,
        }
        self.presence = presence_analyzer
        self.proxy = proxy_guard

    def initialize(self) -> None:
        try:
            self._cap = cv2.VideoCapture(self.camera_id)
            if not self._cap.isOpened():
                raise CameraServiceError(f"Cannot open camera {self.camera_id}")
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.face_engine.initialize()
            logger.info("Camera service initialized")
        except Exception as e:
            raise CameraServiceError(f"Failed to initialize camera service: {e}")

    def close(self) -> None:
        self.stop()
        if self._cap:
            self._cap.release()
            self._cap = None
        # log presence analytics if available
        if self.presence:
            try:
                self.presence.close()
            except Exception:
                pass
        self.face_engine.close()
        logger.info("Camera service closed")

    def start_detection_loop(self, on_attendance_marked=None) -> None:
        if self._running:
            logger.warning("Detection loop already running")
            return
        self._running = True
        self._session_data["start_time"] = datetime.now()
        self._thread = threading.Thread(
            target=self._detection_loop,
            args=(on_attendance_marked,),
            daemon=True,
        )
        self._thread.start()
        logger.info("Detection loop started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        logger.info("Detection loop stopped")

    def _detection_loop(self, on_attendance_marked=None) -> None:
        while self._running and self._cap:
            try:
                frame_start = time.time()
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                results, display_frame = self.face_engine.process_frame(frame)
                if self.proxy:
                    try:
                        results = self.proxy.analyze(frame, results)
                    except Exception as e:
                        logger.debug("proxy guard error: %s", e)
                with self._lock:
                    self._session_data["frame_count"] += 1
                    for result in results:
                        proxy_status = result.get("proxy_status")
                        # do not mark if proxy attempt
                        if proxy_status == "proxy":
                            continue
                        name = result.get("name")
                        confidence = result.get("confidence", 0.0)
                        if name and confidence > 0.65:
                            if name not in self._session_data["marked_today"]:
                                self._session_data["marked_today"][name] = (
                                    datetime.now().isoformat(),
                                    confidence,
                                )
                                if on_attendance_marked:
                                    on_attendance_marked(name, confidence)
                        else:
                            self._session_data["unknown_faces"] += 1
                elapsed = time.time() - frame_start
                if elapsed < self.frame_delay:
                    time.sleep(self.frame_delay - elapsed)
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                continue

    def capture_frame_with_overlay(self) -> Optional[cv2.Mat]:
        if not self._cap:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        results, display_frame = self.face_engine.process_frame(frame)
        for result in results:
            x1, y1, x2, y2 = result.get("box", (0, 0, 0, 0))
            name = result.get("name")
            confidence = result.get("confidence", 0.0)
            status = result.get("status", "")
            presence_time = result.get("presence_time", 0.0)
            proxy_status = result.get("proxy_status")
            # choose color based on proxy status first
            if proxy_status == "proxy":
                color = (0, 0, 255)
            elif proxy_status == "suspicious":
                color = (0, 255, 255)
            else:
                # fall back to behavior status
                if status == "Sleeping":
                    color = (0, 0, 255)
                elif status == AttentionDetector.FOCUSED:
                    color = (0, 255, 0)
                elif status == AttentionDetector.DISTRACTED:
                    color = (0, 255, 255)
                else:
                    color = (255, 255, 255)
            if name and name != "Spoof Detected":
                label = f"{name} {status}"
            elif name == "Spoof Detected":
                color = (0, 0, 255)
                label = "Spoof Detected"
            else:
                color = (0, 0, 255)
                label = "Unknown"
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                display_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )
            # presence time
            cv2.putText(
                display_frame,
                f"{int(presence_time)}s",
                (x1, y2 + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )
        stats = self.face_engine.get_performance_stats()
        fps = stats.get("fps", 0)
        with self._lock:
            marked_count = len(self._session_data["marked_today"])
        info_text = f"FPS: {fps:.1f} | Present: {marked_count} | Unknown: {self._session_data['unknown_faces']}"
        cv2.putText(
            display_frame,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
        return display_frame

    def get_session_stats(self) -> Dict:
        with self._lock:
            uptime = (
                datetime.now() - self._session_data["start_time"]
            ).total_seconds() if self._session_data["start_time"] else 0
            return {
                "uptime_seconds": int(uptime),
                "frames_processed": self._session_data["frame_count"],
                "students_marked": len(self._session_data["marked_today"]),
                "unknown_detected": self._session_data["unknown_faces"],
                "marked_students": list(self._session_data["marked_today"].keys()),
            }

    def get_marked_students(self) -> List[str]:
        with self._lock:
            return list(self._session_data["marked_today"].keys())
