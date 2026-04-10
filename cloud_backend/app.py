from flask import Flask, jsonify, render_template, redirect, request
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# Sample data structure
ATTENDANCE_DATA = {
    "records": [
        {
            "name": "John Doe",
            "date": "2026-04-10",
            "time": "09:30:00",
            "confidence": 0.95,
            "camera_id": "camera_1"
        },
        {
            "name": "Jane Smith",
            "date": "2026-04-10",
            "time": "09:35:00",
            "confidence": 0.92,
            "camera_id": "camera_1"
        }
    ]
}

@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/attendance")
def get_attendance():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    records = ATTENDANCE_DATA["records"]
    total = len(records)
    
    paginated = records[offset:offset+limit]
    
    return jsonify({
        "status": "ok",
        "data": paginated,
        "total": total
    })

@app.route("/api/attendance/today")
def get_attendance_today():
    today = datetime.now().strftime('%Y-%m-%d')
    today_records = [r for r in ATTENDANCE_DATA["records"] if r["date"] == today]
    unique_students = set(r["name"] for r in today_records)
    
    return jsonify({
        "status": "ok",
        "records": today_records,
        "unique_students": len(unique_students),
        "total_records": len(today_records)
    })

@app.route("/api/attendance/export")
def export_attendance():
    return jsonify({
        "status": "ok",
        "data": ATTENDANCE_DATA["records"],
        "export_date": datetime.now().isoformat()
    })

@app.route("/api/stats")
def get_stats():
    total_records = len(ATTENDANCE_DATA["records"])
    today = datetime.now().strftime('%Y-%m-%d')
    today_records = [r for r in ATTENDANCE_DATA["records"] if r["date"] == today]
    
    return jsonify({
        "status": "ok",
        "total_records": total_records,
        "students_marked_today": len(set(r["name"] for r in today_records)),
        "records_today": len(today_records)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    logger.info("Starting Cloud Backend Server...")
    # For production, use gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=False, host='0.0.0.0', port=5000)
