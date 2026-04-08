"""
Attendance API Routes for Cloud Backend
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)

# Data storage path
DATA_DIR = Path(__file__).parent.parent / 'data'
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
        return True
    except Exception as e:
        logger.error(f"Failed to save attendance data: {e}")
        return False


@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance():
    """
    Mark attendance for a student.
    
    Expected JSON payload:
    {
        "name": "Student Name",
        "confidence": 0.95,
        "camera_id": "camera_1",
        "timestamp_iso": "2024-01-01T10:30:00",
        "date": "2024-01-01",
        "time": "10:30:00"
    }
    """
    try:
        payload = request.get_json()
        
        # Validate required fields
        if not payload or 'name' not in payload:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        # Load existing data
        data = load_attendance_data()
        
        # Create record
        record = {
            'name': payload.get('name', '').strip(),
            'confidence': payload.get('confidence', 1.0),
            'camera_id': payload.get('camera_id', 'unknown'),
            'timestamp_iso': payload.get('timestamp_iso', datetime.now().isoformat()),
            'date': payload.get('date', datetime.now().strftime('%Y-%m-%d')),
            'time': payload.get('time', datetime.now().strftime('%H:%M:%S')),
            'sync_timestamp': datetime.now().isoformat(),
            'source': 'local_system'
        }
        
        # Check for duplicates today
        today = record['date']
        today_records = [r for r in data['records'] if r.get('date') == today]
        if any(r.get('name').lower() == record['name'].lower() for r in today_records):
            logger.warning(f"Duplicate attendance prevented for {record['name']} on {today}")
            return jsonify({
                'success': False,
                'message': 'Attendance already marked today for this student',
                'record': record
            }), 200
        
        # Add record to data
        data['records'].append(record)
        
        # Save data
        if save_attendance_data(data):
            logger.info(f"Attendance marked for {record['name']} - confidence: {record['confidence']}")
            return jsonify({
                'success': True,
                'message': 'Attendance marked successfully',
                'record': record
            }), 201
        else:
            return jsonify({'error': 'Failed to save attendance record'}), 500
            
    except Exception as e:
        logger.error(f"Error marking attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('', methods=['GET'])
def get_attendance():
    """
    Get all attendance records with optional filtering.
    
    Query parameters:
    - date: Filter by date (YYYY-MM-DD)
    - camera_id: Filter by camera
    - limit: Limit number of records (default: 1000)
    - offset: Offset for pagination (default: 0)
    """
    try:
        data = load_attendance_data()
        records = data.get('records', [])
        
        # Apply filters
        date_filter = request.args.get('date')
        camera_filter = request.args.get('camera_id')
        limit = int(request.args.get('limit', 1000))
        offset = int(request.args.get('offset', 0))
        
        if date_filter:
            records = [r for r in records if r.get('date') == date_filter]
        
        if camera_filter:
            records = [r for r in records if r.get('camera_id') == camera_filter]
        
        # Sort by date and time (newest first)
        records = sorted(records, 
                        key=lambda x: (x.get('date', ''), x.get('time', '')), 
                        reverse=True)
        
        # Apply pagination
        total = len(records)
        records = records[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'total': total,
            'count': len(records),
            'offset': offset,
            'limit': limit,
            'records': records
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/today', methods=['GET'])
def get_attendance_today():
    """
    Get attendance records for today.
    
    Query parameters:
    - camera_id: Filter by camera
    """
    try:
        data = load_attendance_data()
        records = data.get('records', [])
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_records = [r for r in records if r.get('date') == today]
        
        # Apply camera filter if provided
        camera_filter = request.args.get('camera_id')
        if camera_filter:
            today_records = [r for r in today_records if r.get('camera_id') == camera_filter]
        
        # Get unique students present today
        students_present = {}
        for record in today_records:
            student_name = record.get('name', '')
            if student_name not in students_present:
                students_present[student_name] = record
        
        # Sort by time (newest first)
        sorted_records = sorted(today_records, 
                               key=lambda x: x.get('time', ''), 
                               reverse=True)
        
        return jsonify({
            'success': True,
            'date': today,
            'total_records': len(sorted_records),
            'unique_students': len(students_present),
            'students': list(students_present.keys()),
            'records': sorted_records
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching today's attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get attendance statistics."""
    try:
        data = load_attendance_data()
        records = data.get('records', [])
        
        if not records:
            return jsonify({
                'total_records': 0,
                'unique_students': 0,
                'dates_tracked': 0,
                'most_common_student': None,
                'message': 'No attendance records found'
            }), 200
        
        # Calculate statistics
        total_records = len(records)
        unique_students = len(set(r.get('name', '') for r in records))
        dates_tracked = len(set(r.get('date', '') for r in records))
        
        # Most common student
        student_counts = {}
        for record in records:
            name = record.get('name', '')
            student_counts[name] = student_counts.get(name, 0) + 1
        
        most_common = max(student_counts.items(), key=lambda x: x[1]) if student_counts else (None, 0)
        
        # Average confidence
        confidences = [r.get('confidence', 1.0) for r in records]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return jsonify({
            'total_records': total_records,
            'unique_students': unique_students,
            'dates_tracked': dates_tracked,
            'most_common_student': most_common[0],
            'most_common_count': most_common[1],
            'average_confidence': f"{avg_confidence:.2%}",
            'latest_record_date': max([r.get('date', '') for r in records], default='N/A')
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/export', methods=['GET'])
def export_attendance():
    """Export attendance data as JSON."""
    try:
        data = load_attendance_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error exporting attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
