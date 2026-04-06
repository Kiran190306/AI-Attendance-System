from __future__ import annotations

import logging
import sys

from . import config, utils
from .camera_manager import CameraManager
from .recognition_engine import SharedRecognitionEngine
from .tracker import Tracker
from .events.event_bus import EventBus
from .attendance_service import AttendanceService

logger = logging.getLogger(__name__)


def run_multi_camera() -> int:
    """Entry point for the multi-camera attendance platform."""
    utils.setup_logging(config.LOG_LEVEL)
    logger.info("starting multi-camera attendance system")

    # create shared components
    try:
        engine = SharedRecognitionEngine.get()
    except Exception as exc:
        logger.error("could not create recognition engine: %s", exc)
        return 1

    tracker = Tracker()
    bus = EventBus()
    service = AttendanceService()

    # register attendance service to listen for recognition events
    def _handle_event(ev: dict) -> None:
        name = ev.get("student_name")
        conf = ev.get("confidence", 0.0)
        cam = ev.get("camera_id")
        if name:
            service.mark(name, confidence=conf, camera_id=cam)
        else:
            service.log_unknown_face(confidence=conf, camera_id=cam)

    bus.register(_handle_event)

    # manager is responsible for starting camera threads and display
    manager = CameraManager(engine=engine, tracker=tracker, event_bus=bus)

    try:
        manager.start_all()
        # block until all cameras stop
        while True:
            # main thread simply waits; CameraManager handles quitting when 'q'
            import time

            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("keyboard interrupt, shutting down")
    finally:
        manager.stop_all()
        SharedRecognitionEngine.close()

    return 0


if __name__ == "__main__":
    sys.exit(run_multi_camera())
