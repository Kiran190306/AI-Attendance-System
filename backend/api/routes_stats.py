from flask import Blueprint, jsonify, request
import logging
from datetime import date

from ..services.attendance_service import get_attendance_records

stats_bp = Blueprint("stats", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


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


def _map_record(r):
    name = r.get("name") or r.get("student_name") or ""
    time_val = r.get("time") or (r.get("timestamp_iso") or "")[11:19]
    camera = r.get("camera_name") or r.get("camera") or r.get("camera_id")
    conf = _parse_conf(r.get("confidence"))
    return {
        "student_name": name,
        "date": r.get("date"),
        "time": time_val,
        "camera": camera,
        "confidence": conf,
    }


@stats_bp.route("/stats", methods=["GET"])
def get_stats():
    logger.info("Fetching /api/stats")
    try:
        all_recs = get_attendance_records()
        total_records = len(all_recs)
        today = date.today().isoformat()
        todays_raw = [r for r in all_recs if r.get("date") == today]
        today_records = [_map_record(r) for r in todays_raw]
        present_today = len(today_records)
        confs = [r.get("confidence") for r in today_records if r.get("confidence") is not None]
        avg_confidence = (sum(confs) / len(confs)) if confs else 0.0
        return jsonify({
            "total_records": total_records,
            "present_today": present_today,
            "today_records": today_records,
            "avg_confidence": avg_confidence,
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve statistics"}), 500


