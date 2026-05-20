from flask import Flask, send_from_directory, jsonify, request, redirect
from flask_cors import CORS
from pathlib import Path
import logging

from .utils.logger import setup_logging
from .utils.request_logger import setup_request_logging
from .database.db import init_db
from .services.user_service import verify_token
from .config import CORS_ORIGINS

from .api.routes_auth import auth_bp
from .api.routes_students import students_bp
from .api.routes_attendance import attendance_bp
from .api.routes_analytics import analytics_bp
from .api.routes_stats import stats_bp
from .api.routes_system import system_bp
from .api.routes_mobile import mobile_bp
from .api.routes_training import (
    training_bp,
    add_student as training_add_student,
    train_model as training_train_model,
)
from .api.routes_attendance import export_csv as attendance_export_csv

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# create Flask app
frontend_path = Path(__file__).parent.parent / "frontend"
app = Flask(
    __name__,
    static_folder=str(frontend_path) if frontend_path.exists() else None,
    static_url_path="",
    template_folder=str(frontend_path) if frontend_path.exists() else None,
)
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})
logger.info("CORS enabled for API routes: %s", CORS_ORIGINS)

# Setup request logging middleware
setup_request_logging(app)

logger.info("Application starting up...")

try:
    # Initialize database
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
    # Don't raise - allow app to start even if DB fails
    logger.warning("Continuing without database initialization")

EXEMPT_API_PATHS = {"/api/login", "/api/register", "/api/signup"}

@app.before_request
def require_api_auth():
    if not request.path.startswith("/api/"):
        return

    if request.path in EXEMPT_API_PATHS or request.method == "OPTIONS":
        return

    auth_header = request.headers.get("Authorization", "") or ""
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        payload = request.get_json(silent=True) or {}
        token = request.args.get("token") or payload.get("token")

    if not token:
        return jsonify({"error": "Authorization token required"}), 401

    username = verify_token(token)
    if not username:
        return jsonify({"error": "Invalid or expired token"}), 401

    request.username = username

# register blueprints
logger.info("Registering blueprints...")
for bp in (auth_bp, students_bp, attendance_bp, analytics_bp, stats_bp, system_bp, mobile_bp, training_bp):
    try:
        app.register_blueprint(bp)
        logger.info("Registered blueprint: %s", getattr(bp, "name", str(bp)))
    except Exception as e:
        logger.exception("Failed to register blueprint: %s", e)

logger.info("All blueprints registration attempted")

@app.route("/api/add_student", methods=["POST"], strict_slashes=False)
def api_add_student():
    return training_add_student()


@app.route("/api/train_model", methods=["POST"], strict_slashes=False)
def api_train_model():
    return training_train_model()


@app.route("/api/mark_attendance", methods=["POST"], strict_slashes=False)
def api_mark_attendance():
    logger.info("POST /api/mark_attendance received")
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid payload"}), 400

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
        logger.exception("Error marking attendance: %s", e)
        return jsonify({"error": "Failed to mark attendance"}), 500

logger.info("Route /api/mark_attendance registered")

# Add a simple test route
@app.route("/api/test", methods=["GET"])
def test_route():
    return jsonify({"status": "ok", "message": "API is working"}), 200

logger.info("Route /api/test registered")

# Add get_attendance route (alias for /api/attendance)
@app.route("/api/get_attendance", methods=["GET"])
def get_attendance_route():
    from flask import redirect
    query = request.query_string.decode("utf-8")
    target = "/api/attendance" + (f"?{query}" if query else "")
    return redirect(target)



@app.route('/api/export_csv', methods=['GET'])
def export_csv_alias():
    # top-level alias for CSV export: forwards to attendance blueprint exporter
    return attendance_export_csv()

logger.info("Route /api/get_attendance registered")


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Basic liveness
        return jsonify({"status": "ok"}), 200
    except Exception:
        return jsonify({"status": "error"}), 500

# route root to dashboard page
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "dashboard.html")

# Add student page
@app.route("/add_student")
def add_student():
    return send_from_directory(app.static_folder, "add_student.html")

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

@app.route('/login')
def login_page():
    return send_from_directory(app.static_folder, "login.html")

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, "dashboard.html"), 200
