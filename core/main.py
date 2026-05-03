from __future__ import annotations

import logging
import sys
import time
from datetime import datetime

import cv2
import numpy as np

from . import config, utils
from .face_engine import FaceRecognitionEngine, FaceRecognitionEngineError
from .attendance_service import AttendanceService
from .voice_engine import VoiceEngine

logger = logging.getLogger(__name__)


def run_attendance() -> int:
    """Main entry point for the real-time attendance application."""
    utils.setup_logging(config.LOG_LEVEL)
    logger.info("starting attendance application")

    try:
        engine = FaceRecognitionEngine(target_frame_width=640)
        engine.initialize()
    except FaceRecognitionEngineError as exc:
        logger.error("failed to initialise face engine: %s", exc)
        return 1
    except Exception as exc:  # pragma: no cover
        logger.exception("unexpected error while initialising engine")
        return 1

    service = AttendanceService()
    voice_engine = VoiceEngine()
    # store voice status messages for display: name -> (text, timestamp, color)
    voice_feedback: dict[str, tuple[str, float, tuple[int,int,int]]] = {}

    def make_voice_callback(captured_name: str, face_conf: float):
        def _cb(name: str, command: str, status: str, valid: bool) -> None:
            # update overlay
            color = (0, 255, 0) if valid else (0, 0, 255)
            voice_feedback[name] = (status, time.time(), color)
            if valid:
                # use the confidence that triggered the request
                service.mark(name, confidence=face_conf)
                logger.info("voice verified attendance for %s", name)
            else:
                logger.info("voice verification failed for %s: %s", name, status)
        return _cb

    try:
        cap = utils.open_camera()
    except RuntimeError as exc:
        logger.error("camera error: %s", exc)
        return 1

    logger.info("beginning video capture loop (press 'q' to quit)")
    frame_count = 0
    stats_print_interval = 60
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning("empty frame received, terminating")
                break

            frame_count += 1
            
            # cleanup expired voice feedback entries (older than 5s)
            now_ts = time.time()
            expired = [n for n, (_, ts, _) in voice_feedback.items() if now_ts - ts > 5]
            for n in expired:
                del voice_feedback[n]

            # Process frame (returns results + resized display frame)
            results, display_frame = engine.process_frame(frame)
            h, w = display_frame.shape[:2]
            
            # Draw detected faces
            for face in results:
                x1, y1, x2, y2 = face["box"]
                name = face["name"]
                conf = face["confidence"]
                
                if name:
                    # recognized face; ensure voice verification request sent
                    if not service.is_marked(name) and name not in voice_engine.pending:
                        # prompt user
                        logger.info("face recognized for %s, prompting voice confirmation", name)
                        print("Please say present")  # console prompt
                        voice_feedback[name] = ("Listening...", now_ts, (0, 255, 255))
                        voice_engine.request(name, make_voice_callback(name, conf))

                    # display face box
                    color = (0, 255, 0)  # green
                    label = f"{name} {conf:.0%}"
                    utils.draw_box_with_label(
                        display_frame, x1, y1, x2, y2, label, color, thickness=2
                    )

                    # determine status badge text & color
                    if name in voice_feedback:
                        status_text, _, status_color = voice_feedback[name]
                        utils.draw_status_badge(
                            display_frame, status_text, x1, y2 + 20, status_color
                        )
                    else:
                        # still awaiting or already marked
                        if service.is_marked(name):
                            status_text = "[OK] MARKED"
                            utils.draw_status_badge(
                                display_frame, status_text, x1, y2 + 20, color
                            )

                    logger.debug("recognized: %s (%.0f%%)", name, conf * 100)
                else:
                    # Unknown face
                    service.log_unknown_face(confidence=conf)
                    color = (0, 0, 255)  # red
                    label = "Unknown"
                    
                    utils.draw_box_with_label(
                        display_frame, x1, y1, x2, y2, label, color, thickness=2
                    )
                    logger.debug("unknown face detected")
            
            # Attendance stats panel (top-left)
            att_stats = service.get_session_stats()
            att_info = [
                f"Recognized: {att_stats['recognized_count']}",
                f"Unknown: {att_stats['unknown_count']}",
                f"Marked: {att_stats['marked_today']}",
                f"Duplicates blocked: {att_stats['duplicates_prevented']}",
            ]
            utils.draw_info_panel(
                display_frame,
                "ATTENDANCE",
                att_info,
                position="top-left",
                bg_color=(30, 30, 80),  # dark blue
            )
            
            # Performance stats panel (top-right)
            stats = engine.get_performance_stats()
            perf_info = [
                f"FPS: {stats['fps']}",
                f"Frame: {stats['avg_frame_time_ms']}ms",
                f"Detect: {stats['avg_detection_time_ms']}ms",
                f"Recog: {stats['avg_recognition_time_ms']}ms",
                f"Students: {stats['enrolled_students']}",
            ]
            utils.draw_info_panel(
                display_frame,
                "PERFORMANCE",
                perf_info,
                position="top-right",
                bg_color=(30, 80, 30),  # dark green
            )
            
            # Recent activity panel (bottom-left)
            recent = service.get_recent_activity(limit=5)
            recent_info = []
            for entry in recent:
                s = f"{entry['name'][:15]:<15} {entry['timestamp']} {entry['status']}"
                recent_info.append(s)
            
            if recent_info:
                utils.draw_info_panel(
                    display_frame,
                    "RECENT",
                    recent_info,
                    position="bottom-left",
                    bg_color=(50, 50, 50),  # dark gray
                )
            
            # Instruction text
            utils.draw_instruction_text(
                display_frame,
                "Press 'Q' to quit | 'R' to reset session",
                position="bottom",
            )
            
            # Display
            cv2.imshow("AI Attendance System", display_frame)
            
            # Handle input
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("user requested quit")
                break
            elif key == ord("r"):
                logger.info("resetting session")
                service.reset_session()
            
            # Print detailed stats periodically
            if frame_count % stats_print_interval == 0:
                logger.info(
                    "session stats: recognized=%d, unknown=%d, marked=%d, fps=%.1f",
                    att_stats["recognized_count"],
                    att_stats["unknown_count"],
                    att_stats["marked_today"],
                    stats["fps"],
                )
    except KeyboardInterrupt:
        logger.info("user interruption")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        engine.close()
        
        # Final comprehensive stats
        final_stats = engine.get_performance_stats()
        final_att_stats = service.get_session_stats()
        
        logger.info("=" * 60)
        logger.info("SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info("Attendance Stats:")
        logger.info("  - Total recognized: %d", final_att_stats["recognized_count"])
        logger.info("  - Unknown faces: %d", final_att_stats["unknown_count"])
        logger.info("  - Students marked today: %d", final_att_stats["marked_today"])
        logger.info("  - Duplicates prevented: %d", final_att_stats["duplicates_prevented"])
        logger.info("Performance Stats:")
        logger.info("  - Average FPS: %.1f", final_stats["fps"])
        logger.info("  - Average frame time: %.2fms", final_stats["avg_frame_time_ms"])
        logger.info("  - Average detection time: %.2fms", final_stats["avg_detection_time_ms"])
        logger.info("  - Average recognition time: %.2fms", final_stats["avg_recognition_time_ms"])
        logger.info("  - Total frames processed: %d", frame_count)
        logger.info("  - Enrolled students: %d", final_stats["enrolled_students"])
        logger.info("Attendance Data:")
        logger.info("  - Database Location: %s", config.ATTENDANCE_DB)
        logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(run_attendance())
