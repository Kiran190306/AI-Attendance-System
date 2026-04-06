from flask import Flask, send_from_directory
from flask_cors import CORS
from pathlib import Path

from .utils.logger import setup_logging

from .api.routes_students import students_bp
from .api.routes_attendance import attendance_bp
from .api.routes_system import system_bp
from .api.routes_mobile import mobile_bp

# create Flask app
app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path="",
    template_folder="../frontend",
)
CORS(app)

setup_logging()

# register blueprints
app.register_blueprint(students_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(system_bp)
app.register_blueprint(mobile_bp)

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
