from flask import Flask, jsonify, render_template, redirect, request, session, url_for
from datetime import datetime
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'ai-attendance-system-secret-key-2026'  # Change this in production

DATABASE = os.path.join(os.path.dirname(__file__), 'attendance.db')


def get_db():
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = get_db()
    with conn:
        # Create users table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create attendance table with user_id
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        # Create default admin user if not exists
        admin_exists = conn.execute("SELECT 1 FROM users WHERE username = 'admin'").fetchone()
        if not admin_exists:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ("admin", "1234")
            )
            logger.info("Default admin user created")

    conn.close()


init_db()

@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/debug")
def debug():
    """Debug route to check app status."""
    return jsonify({
        "status": "ok",
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
        "session_logged_in": session.get("logged_in", False)
    })

@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle login page and authentication."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Validate user from database
        with get_db() as conn:
            user = conn.execute(
                "SELECT id, username FROM users WHERE username = ? AND password = ?",
                (username, password)
            ).fetchone()

        if user:
            session["logged_in"] = True
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            logger.info(f"User {username} (ID: {user['id']}) logged in successfully")
            return redirect("/dashboard")
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template("login.html", error="Invalid username or password")

    # If already logged in, redirect to dashboard
    if session.get("logged_in"):
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Handle logout."""
    session.clear()
    logger.info("User logged out")
    return redirect("/login")

@app.route("/api/signup", methods=["POST"])
def signup():
    """Handle user registration."""
    try:
        data = request.json
        if not data or "username" not in data or "password" not in data:
            return jsonify({"status": "error", "message": "Missing username or password"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password cannot be empty"}), 400

        if len(username) < 3 or len(password) < 4:
            return jsonify({"status": "error", "message": "Username must be at least 3 characters, password at least 4"}), 400

        with get_db() as conn:
            # Check if username already exists
            existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                return jsonify({"status": "error", "message": "Username already exists"}), 409

            # Create new user
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        logger.info(f"New user created: {username} (ID: {user_id})")
        return jsonify({
            "status": "success",
            "message": "User created successfully",
            "user_id": user_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    """Protected dashboard route."""
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    """Receive attendance data from local system and store it in SQLite."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    try:
        data = request.json
        if not data or "name" not in data:
            return jsonify({"status": "error", "message": "Missing required field: name"}), 400

        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Name cannot be empty"}), 400

        status = data.get("status", "present").strip().lower() or "present"
        date_value = data.get("date")
        time_value = data.get("time")
        user_id = session.get("user_id")

        if date_value and time_value:
            attendance_time = f"{date_value} {time_value}"
        elif time_value:
            if isinstance(time_value, str) and time_value.count(":") == 2 and len(time_value) == 8:
                attendance_time = f"{datetime.now().strftime('%Y-%m-%d')} {time_value}"
            else:
                attendance_time = time_value
        else:
            attendance_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        today = attendance_time.split(" ")[0]
        with get_db() as conn:
            duplicate = conn.execute(
                "SELECT 1 FROM attendance WHERE user_id = ? AND LOWER(name) = ? AND time LIKE ? LIMIT 1",
                (user_id, name.lower(), f"{today}%")
            ).fetchone()
            if duplicate:
                logger.info(f"Duplicate prevented for {name} on {today} (user_id: {user_id})")
                return jsonify({
                    "status": "duplicate",
                    "message": "Attendance already marked today",
                    "record": {
                        "name": name,
                        "time": attendance_time,
                        "status": status
                    }
                }), 200

            conn.execute(
                "INSERT INTO attendance (user_id, name, time, status) VALUES (?, ?, ?, ?)",
                (user_id, name, attendance_time, status)
            )

        logger.info(f"Attendance marked: {name} at {attendance_time} (status: {status}, user_id: {user_id})")
        return jsonify({
            "status": "success",
            "message": "Attendance marked successfully",
            "record": {
                "name": name,
                "time": attendance_time,
                "status": status
            }
        }), 200
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/attendance")
def get_attendance():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    user_id = session.get("user_id")

    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ?", (user_id,)).fetchone()[0]
        rows = conn.execute(
            "SELECT id, name, time, status FROM attendance WHERE user_id = ? ORDER BY time DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        ).fetchall()

    return jsonify({
        "status": "ok",
        "data": [dict(row) for row in rows],
        "total": total
    })


@app.route("/api/attendance/today")
def get_attendance_today():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    today = datetime.now().strftime('%Y-%m-%d')
    user_id = session.get("user_id")

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, time, status FROM attendance WHERE user_id = ? AND time LIKE ? ORDER BY time DESC",
            (user_id, f"{today}%")
        ).fetchall()

    today_records = [dict(row) for row in rows]
    unique_students = set(r.get("name", "") for r in today_records if r.get("name"))

    return jsonify({
        "status": "ok",
        "records": today_records,
        "unique_students": len(unique_students),
        "total_records": len(today_records)
    })


@app.route("/api/attendance/export")
def export_attendance():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    user_id = session.get("user_id")

    with get_db() as conn:
        rows = conn.execute("SELECT id, name, time, status FROM attendance WHERE user_id = ? ORDER BY time DESC", (user_id,)).fetchall()

    return jsonify({
        "status": "ok",
        "data": [dict(row) for row in rows],
        "export_date": datetime.now().isoformat(),
        "total_records": len(rows)
    })


@app.route("/api/stats")
def get_stats():
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    today = datetime.now().strftime('%Y-%m-%d')
    user_id = session.get("user_id")

    with get_db() as conn:
        total_records = conn.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ?", (user_id,)).fetchone()[0]
        today_rows = conn.execute(
            "SELECT name FROM attendance WHERE user_id = ? AND time LIKE ?",
            (user_id, f"{today}%")
        ).fetchall()

    unique_today = set(row[0] for row in today_rows if row[0])

    return jsonify({
        "status": "ok",
        "total_records": total_records,
        "students_marked_today": len(unique_today),
        "records_today": len(today_rows)
    })


@app.route("/api/analytics")
def get_analytics():
    """Get analytics data for dashboard."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    today = datetime.now().strftime('%Y-%m-%d')
    user_id = session.get("user_id")

    with get_db() as conn:
        total_records = conn.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ?", (user_id,)).fetchone()[0]
        today_rows = conn.execute(
            "SELECT name, time, status FROM attendance WHERE user_id = ? AND time LIKE ? ORDER BY time DESC",
            (user_id, f"{today}%")
        ).fetchall()

    today_records = [dict(row) for row in today_rows]
    unique_students_today = set(r.get("name", "") for r in today_records if r.get("name"))
    present_today = sum(1 for r in today_records if r.get("status", "").lower() == "present")

    # Get total unique students for this user
    with get_db() as conn:
        all_students = conn.execute("SELECT DISTINCT name FROM attendance WHERE user_id = ?", (user_id,)).fetchall()

    total_students = len([row[0] for row in all_students if row[0]])
    attendance_percentage = round((present_today / total_students * 100) if total_students > 0 else 0, 1)

    return jsonify({
        "total": total_students,
        "present": present_today,
        "attendance_percentage": attendance_percentage
    })

@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "AI Attendance Cloud Backend",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    logger.info("Starting Cloud Backend Server...")
    # For production, use gunicorn: gunicorn -w 4 -b 0.0.0.0:10000 app:app
    app.run(debug=False, host='127.0.0.1', port=10000)
