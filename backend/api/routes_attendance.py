from flask import Blueprint, jsonify, request
from pathlib import Path
import logging
from ..database.db import SessionLocal
from ..database.repository import AttendanceRepository

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")
logger = logging.getLogger(__name__)


def _entry_to_dict(entry):
    return {
        "student_name": entry.student_name,
        "date": entry.date.isoformat(),
        "time": getattr(entry, "time", entry.timestamp.strftime("%H:%M:%S")),
        "camera": getattr(entry, "camera", None),
        "confidence": entry.confidence,
    }


@attendance_bp.route("", methods=["GET"], strict_slashes=False)
def get_attendance():
    logger.info("GET /api/attendance received")
    # if download query provided, send raw CSV
    if request.args.get("download"):
        # serve the underlying CSV file
        from flask import send_file
        path = Path("attendance/attendance.csv")
        if path.exists():
            logger.info("Downloading attendance CSV file")
            return send_file(path, as_attachment=True)
        logger.warning("Attendance CSV file not found")
        return jsonify({"error": "file not found"}), 404

    date_filter = request.args.get("date")
    try:
        # Prefer CSV-backed records (contains camera info). Fall back to DB if CSV missing.
        from ..services.attendance_service import get_attendance_records

        def _parse_conf(conf):
            if conf is None:
                return None
            try:
                if isinstance(conf, str) and conf.strip().endswith("%"):
                    return float(conf.strip().strip("%")) / 100.0
                v = float(conf)
                return v if v <= 1.0 else v / 100.0
            except Exception:
                return None

        csv_recs = get_attendance_records(date_filter) if date_filter else get_attendance_records()
        if csv_recs:
            mapped = []
            for r in csv_recs:
                name = r.get("name") or r.get("student_name") or ""
                time_val = r.get("time") or (r.get("timestamp_iso") or "")[11:19]
                camera = r.get("camera_name") or r.get("camera") or r.get("camera_id")
                confidence = _parse_conf(r.get("confidence"))
                mapped.append({
                    "student_name": name,
                    "date": r.get("date"),
                    "time": time_val,
                    "camera": camera,
                    "confidence": confidence,
                })
            logger.info(f"Retrieved {len(mapped)} attendance records (CSV)")
            return jsonify(mapped)

        # fallback to DB
        db = SessionLocal()
        try:
            all_recs = AttendanceRepository.list_all(db)
            if date_filter:
                all_recs = [r for r in all_recs if r.date.isoformat() == date_filter]
                logger.info(f"Retrieved {len(all_recs)} attendance records for date: {date_filter} (DB)")
            else:
                logger.info(f"Retrieved {len(all_recs)} total attendance records (DB)")
            return jsonify([_entry_to_dict(r) for r in all_recs])
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching attendance records: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve attendance records"}), 500


@attendance_bp.route("/today", methods=["GET"])
def get_today():
    logger.info("Fetching today's attendance statistics")
    # return summarized stats rather than raw list
    from ..services.attendance_service import get_today_stats, get_summary
    try:
        stats = get_today_stats()
        summary = get_summary()
        stats["total_students"] = summary.get("total_students", 0)
        logger.info(f"Today's stats: {stats}")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching today's stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve today's statistics"}), 500
    return jsonify(stats)
