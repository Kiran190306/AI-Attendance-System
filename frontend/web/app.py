"""
Flask web dashboard for AI Attendance System.
Provides web interface to view attendance records, student list, and download data.
"""

import csv
import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, send_file, request
import sys

# Add parent directory to path to import core package
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.attendance_service import AttendanceService
from core.config import ATTENDANCE_DB, DATASET_PATH
from core.dataset_loader import DatasetLoader


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize services
    attendance_service = AttendanceService()
    
    # ======================================================================
    # Routes
    # ======================================================================
    
    @app.route('/')
    def dashboard():
        """Main dashboard - today's attendance."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's attendance
        records = attendance_service.get_records(date_str=today)
        
        # Get session stats
        stats = attendance_service.get_session_stats()
        
        # Get student list for total count
        try:
            loader = DatasetLoader()
            students = loader.get_student_list()
            total_students = len(students)
        except Exception:
            total_students = 0
        
        # Prepare data for dashboard
        today_attendance = []
        for record in records[::-1]:  # Reverse to show latest first
            today_attendance.append({
                'time': record['time'],
                'name': record['name'],
                'confidence': record.get('confidence', '0%'),
                'timestamp': record['timestamp_iso']
            })
        
        return render_template('dashboard.html',
                             today_date=today,
                             total_students=total_students,
                             marked_today=len(records),
                             records=today_attendance,
                             stats=stats)
    
    
    @app.route('/students')
    def students():
        """View all enrolled students."""
        try:
            loader = DatasetLoader()
            student_list = loader.get_student_list()
            stats = loader.get_statistics()
            
            students_data = []
            for student_name in student_list:
                student_stats = stats['per_student'].get(student_name, {})
                students_data.append({
                    'name': student_name,
                    'images_found': student_stats.get('images_found', 0),
                    'images_processed': student_stats.get('images_processed', 0),
                    'status': 'OK' if student_stats.get('images_processed', 0) > 0 else 'NO FACES'
                })
            
        except Exception as e:
            students_data = []
        
        return render_template('students.html', 
                             students=students_data,
                             total_count=len(students_data))
    
    
    @app.route('/records')
    def records():
        """View all attendance records."""
        # Get all records from database
        records_list = attendance_service.get_records(limit=1000)  # Get more records for the records page
        
        # Format for display
        formatted_records = []
        for record in records_list:
            formatted_records.append({
                'date': record.get('date', ''),
                'time': record.get('time', ''),
                'name': record.get('name', ''),
                'confidence': record.get('confidence', '0%'),
                'timestamp': record.get('timestamp_iso', '')
            })
        
        # Reverse to show latest first
        formatted_records = formatted_records[::-1]
        
        # Get date filter from query string
        date_filter = request.args.get('date', '')
        
        if date_filter:
            formatted_records = [r for r in formatted_records if r['date'] == date_filter]
        
        # Get unique dates for filter
        dates = sorted(set(r['date'] for r in formatted_records if r['date']), reverse=True)
        
        return render_template('records.html',
                             records=records_list,
                             total_count=len(records_list),
                             dates=dates,
                             selected_date=date_filter)
    
    
    @app.route('/api/stats')
    def api_stats() -> Dict[str, Any]:
        """API endpoint for attendance statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        records = AttendanceService().get_records(date_str=today)
        
        try:
            loader = DatasetLoader()
            students = loader.get_student_list()
        except Exception:
            students = []
        
        return jsonify({
            'today_date': today,
            'marked_today': len(records),
            'total_students': len(students),
            'marked_percentage': f"{(len(records) / len(students) * 100):.1f}%" if students else "0%"
        })
    
    
    @app.route('/api/records/<date_str>')
    def api_records_by_date(date_str: str) -> Dict[str, Any]:
        """API endpoint for records by date."""
        service = AttendanceService()
        records = service.get_records(date_str=date_str)
        
        records_data = [
            {
                'time': r['time'],
                'name': r['name'],
                'confidence': float(r['confidence'].strip('%')) / 100 if r.get('confidence') else 0.0
            }
            for r in records
        ]
        
        return jsonify({
            'date': date_str,
            'total': len(records_data),
            'records': records_data
        })
    
    
    @app.route('/download-csv')
    def download_csv():
        """Download attendance CSV file."""
        try:
            import io
            
            # Get all records from database
            records = attendance_service.get_records(limit=10000)  # Get all records
            
            if not records:
                return jsonify({'error': 'No attendance records found'}), 404
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=['id', 'name', 'time', 'status', 'date', 'confidence', 'camera_id', 'timestamp_iso']
            )
            writer.writeheader()
            
            for record in records:
                # Convert confidence back to decimal for CSV
                csv_record = record.copy()
                if 'confidence' in csv_record and csv_record['confidence']:
                    try:
                        csv_record['confidence'] = f"{float(csv_record['confidence'].strip('%')) / 100:.2%}"
                    except:
                        pass
                writer.writerow(csv_record)
            
            # Create response
            output.seek(0)
            response_data = output.getvalue()
            output.close()
            
            # Return as downloadable file
            return send_file(
                io.BytesIO(response_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'attendance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'attendance_db_exists': ATTENDANCE_DB.exists(),
            'dataset_path_exists': DATASET_PATH.exists()
        })
    
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
