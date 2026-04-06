from flask import Blueprint, jsonify, request
from pathlib import Path
from ..database.db import SessionLocal
from ..database.repository import AttendanceRepository

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


def _entry_to_dict(entry):
    return {
        "student_name": entry.student_name,
        "date": entry.date.isoformat(),
        "timestamp": entry.timestamp.isoformat(),
        "confidence": entry.confidence,
    }


@attendance_bp.route("", methods=["GET"])
def get_attendance():
    # if download query provided, send raw CSV
    if request.args.get("download"):
        # serve the underlying CSV file
        from flask import send_file
        path = Path("attendance/attendance.csv")
        if path.exists():
            return send_file(path, as_attachment=True)
        return jsonify({"error": "file not found"}), 404

    date_filter = request.args.get("date")
    db = SessionLocal()
    try:
        # fetch all and optionally filter by date string (DB based)
        all_recs = AttendanceRepository.list_all(db)
        if date_filter:
            all_recs = [r for r in all_recs if r.date.isoformat() == date_filter]
        return jsonify([_entry_to_dict(r) for r in all_recs])
    finally:
        db.close()


@attendance_bp.route("/today", methods=["GET"])
def get_today():
    # return summarized stats rather than raw list
    from ..services.attendance_service import get_today_stats, get_summary
    stats = get_today_stats()
    summary = get_summary()
    stats["total_students"] = summary.get("total_students", 0)
    return jsonify(stats)
