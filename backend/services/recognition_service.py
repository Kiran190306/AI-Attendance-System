from typing import Tuple, List, Dict

from ..core.face_engine import FaceRecognitionEngine
from ..core.attendance_service import AttendanceService


class RecognitionService:
    def __init__(
        self,
        engine: FaceRecognitionEngine,
        attendance_service: AttendanceService,
    ):
        self.engine = engine
        self.attendance_service = attendance_service

    def process_frame(self, frame) -> Tuple[List[Dict], any]:
        results, display = self.engine.process_frame(frame)
        for r in results:
            name = r.get("name")
            conf = r.get("confidence", 0.0)
            if name:
                self.attendance_service.mark(name, confidence=conf)
            else:
                self.attendance_service.log_unknown(confidence=conf)
        return results, display
