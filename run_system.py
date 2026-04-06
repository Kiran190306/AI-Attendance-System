#!/usr/bin/env python3
"""
Run the AI Attendance System - Face Recognition & API Server.

This script starts:
1. SQLite Database initialization
2. FastAPI backend server
3. Real-time face recognition and camera service
4. Web dashboard

Usage:
    python run_system.py
"""
import os
import sys
import cv2
import logging
import webbrowser
import time
import threading
from pathlib import Path
from datetime import datetime

# make sure backend package is importable
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import init_db, SessionLocal
from backend.database.repository import AttendanceRepository
from backend.core.face_engine import FaceRecognitionEngine
from backend.core.camera_service import CameraService
from backend.core.attendance_service import AttendanceService
from backend.core.presence_analyzer import SmartPresenceAnalyzer
from backend.core.proxy_guard import ProxyGuard
from backend.analytics.session_logger import SessionLogger
from backend.app import app as flask_app
# distance recognition engine (optional)
from backend.core.distance_recognition import DistanceRecognitionEngine
from backend.core.face_engine import FaceRecognitionEngine
# analytics dashboard
from web import dashboard as analytics

# Flask will serve; no uvicorn needed


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AttendanceSystem:
    """Main attendance system orchestrator."""

    def __init__(self):
        self.face_engine = None
        self.camera_service = None
        self.attendance_service = None
        self.running = False

    def initialize(self):
        """Initialize all system components."""
        logger.info("=" * 70)
        logger.info("AI Attendance System Startup")
        logger.info("=" * 70)

        # Create necessary directories
        Path("dataset").mkdir(exist_ok=True)
        Path("attendance").mkdir(exist_ok=True)

        logger.info("✓ Initializing database...")
        init_db()
        logger.info("✓ Database initialized")

        logger.info("✓ Loading face recognition engine...")
        # choose engine based on env flag
        use_distance = os.getenv("DISTANCE_MODE", "0") in ("1","true","True")
        try:
            if use_distance:
                logger.info("Using DistanceRecognitionEngine (long-distance mode)")
                self.face_engine = DistanceRecognitionEngine(
                    dataset_path="dataset",
                    frame_skip=2,
                    target_frame_width=1280,
                )
            else:
                self.face_engine = FaceRecognitionEngine(
                    dataset_path="dataset",
                    detection_confidence=0.7,
                    match_threshold=0.6,
                    recognition_confidence=0.65,
                    target_frame_width=640,
                    frame_skip=2,
                )
            self.face_engine.initialize()
            logger.info("✓ Face engine initialized")
            # student list method may differ
            try:
                students = self.face_engine.get_student_list()
            except Exception:
                students = []
            logger.info(f"  - Enrolled students: {len(students)}")
        except Exception as e:
            logger.error(f"✗ Failed to initialize face engine: {e}")
            raise

        logger.info("✓ Initializing attendance service...")
        self.attendance_service = AttendanceService()
        logger.info("✓ Attendance service ready")

        logger.info("✓ Initializing camera service...")
        try:
            # create presence intelligence and session logger
            presence_logger = SessionLogger()
            presence_analyzer = SmartPresenceAnalyzer(logger_obj=presence_logger)
            proxy = ProxyGuard(dataset_path="dataset")
            self.camera_service = CameraService(
                face_engine=self.face_engine,
                camera_id=0,
                target_fps=15,
                presence_analyzer=presence_analyzer,
                proxy_guard=proxy,
            )
            self.camera_service.initialize()
            logger.info("✓ Camera service initialized with presence analyzer")
        except Exception as e:
            logger.error(f"✗ Failed to initialize camera service: {e}")
            self.camera_service = None

        logger.info("=" * 70)


    def start_camera_loop(self):
        """Start real-time face detection loop."""
        if not self.camera_service:
            logger.warning("Camera service not available - skipping camera loop")
            return

        logger.info("Starting real-time face detection loop...")
        logger.info("Press 'Q' to stop camera")

        self.camera_service.start_detection_loop(
            on_attendance_marked=self.attendance_service.mark
        )

        try:
            while self.running:
                frame = self.camera_service.capture_frame_with_overlay()
                if frame is None:
                    continue

                cv2.imshow("AI Attendance System - Real-time Detection", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q') or key == 27:  # Q or ESC
                    logger.info("Stopping camera...")
                    break

        except KeyboardInterrupt:
            logger.info("Interrupted...")
        finally:
            self.camera_service.stop()
            cv2.destroyAllWindows()

    def start_api_server(self):
        """Start Flask API server in a thread."""
        logger.info("Starting Flask API server on http://localhost:5000")
        # run the built-in development server; in prod use gunicorn
        flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up...")

        if self.camera_service:
            # presence analytics will be flushed by camera_service.close()
            self.camera_service.close()

        if self.face_engine:
            self.face_engine.close()

        logger.info("✓ Cleanup complete")

    def start_analytics_server(self):
        """Run the analytics dashboard Flask app."""
        logger.info("Starting analytics dashboard on http://localhost:5001")
        analytics.app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)

    def run(self):
        """Run the attendance system."""
        self.running = True

        try:
            self.initialize()

            # Start API server in a background thread
            api_thread = threading.Thread(target=self.start_api_server, daemon=True)
            api_thread.start()

            # start analytics dashboard as well
            dash_thread = threading.Thread(target=self.start_analytics_server, daemon=True)
            dash_thread.start()

            # Give servers time to start
            time.sleep(2)

            # Open dashboard(s) in browser
            logger.info("Opening web dashboard in browser...")
            try:
                webbrowser.open("http://localhost:5000/")
                webbrowser.open("http://localhost:5001/")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")

            # Start camera loop in main thread
            self.start_camera_loop()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.running = False
            self.cleanup()
            logger.info("=" * 70)
            logger.info("System shutdown complete")
            logger.info("=" * 70)


def print_banner():
    """Print system banner."""
    banner = r"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║      🎓 AI ATTENDANCE SYSTEM - FACE RECOGNITION PLATFORM 🎓      ║
    ║                                                                   ║
    ║              Production-Grade Attendance Tracking                 ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point."""
    print_banner()

    system = AttendanceSystem()
    system.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSystem shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
