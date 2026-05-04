from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from pathlib import Path
import logging

from .utils.logger import setup_logging
from .utils.request_logger import setup_request_logging
from .database.db import init_db

from .api.routes_auth import auth_bp
from .api.routes_students import students_bp
from .api.routes_attendance import attendance_bp
from .api.routes_analytics import analytics_bp
from .api.routes_stats import stats_bp
from .api.routes_system import system_bp
from .api.routes_mobile import mobile_bp

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# create Flask app
app = Flask(
    __name__,
    static_folder="..//frontend",
    static_url_path="",
    template_folder="..//frontend",
)
CORS(app, resources={r"/api/*": {"origins": "*"}})
logger.info("CORS enabled for API routes")

# Setup request logging middleware
setup_request_logging(app)

logger.info("Application starting up...")

try:
    # Initialize database
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
    raise

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(system_bp)
app.register_blueprint(mobile_bp)

logger.info("All blueprints registered")

@app.route("/api/mark_attendance", methods=["POST"], strict_slashes=False)
def api_mark_attendance():
    logger.info("POST /api/mark_attendance received")
    try:
        payload = request.get_json(force=True)
        logger.info("POST /api/mark_attendance payload: %s", payload)
        if not payload:
            return jsonify({"error": "invalid payload"}), 400

        logger.info("Received payload: %s", payload)
        name = payload.get("student_name") or payload.get("name")
        if not name:
            return jsonify({"error": "student_name required"}), 400

        confidence = payload.get("confidence", 1.0)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 1.0
        camera = payload.get("camera") or payload.get("camera_name")

        from .core.attendance_service import AttendanceService

        service = AttendanceService()
        marked = service.mark(name, confidence=confidence, camera_name=camera)
        return jsonify({"marked": bool(marked)}), (200 if marked else 409)
    except Exception as e:
        logger.error(f"Error marking attendance: {e}", exc_info=True)
        return jsonify({"error": "Failed to mark attendance"}), 500

# route root to dashboard page
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "dashboard.html")

# serve mobile web app
@app.route("/mobile")
def mobile_index():
    return send_from_directory(str(Path(__file__).parent.parent / 'mobile'), "mobile_app.html")

@app.route("/mobile/<path:path>")
def mobile_static(path):
    return send_from_directory(str(Path(__file__).parent.parent / 'mobile'), path)

# serve other html pages explicitly
@app.route("/students")
def students_page():
    return send_from_directory(app.static_folder, "students.html")

@app.route("/attendance")
def attendance_page():
    return send_from_directory(app.static_folder, "attendance.html")

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, "dashboard.html"), 200
