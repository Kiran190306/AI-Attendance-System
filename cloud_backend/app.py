"""
Cloud Backend API for AI Attendance System
Hybrid Cloud Deployment - Cloud Side
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
CORS(app)  # Enable CORS for all routes

# Data storage path
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
ATTENDANCE_FILE = DATA_DIR / 'attendance.json'


def load_attendance_data():
    """Load attendance data from JSON file."""
    if ATTENDANCE_FILE.exists():
        try:
            with open(ATTENDANCE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load attendance data: {e}")
            return {"records": []}
    return {"records": []}


def save_attendance_data(data):
    """Save attendance data to JSON file."""
    try:
        with open(ATTENDANCE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("Attendance data saved successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to save attendance data: {e}")
        return False


# Import routes
from cloud_backend.routes.attendance_routes import attendance_bp

app.register_blueprint(attendance_bp, url_prefix='/api/attendance')


@app.route('/', methods=['GET'])
def dashboard():
    """Render the dashboard."""
    return render_template('dashboard.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'service': 'AI Attendance System - Cloud Backend'
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get attendance statistics."""
    data = load_attendance_data()
    records = data.get('records', [])
    
    # Calculate statistics
    total_records = len(records)
    today = datetime.now().strftime('%Y-%m-%d')
    today_records = [r for r in records if r.get('date') == today]
    
    students_today = set(r.get('name', '') for r in today_records)
    
    stats = {
        'total_records': total_records,
        'students_marked_today': len(students_today),
        'records_today': len(today_records),
        'last_updated': max([r.get('timestamp_iso', '') for r in records], default='Never')
    }
    
    return jsonify(stats), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    logger.info("Starting Cloud Backend Server...")
    # For production, use gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=False, host='0.0.0.0', port=5000)
