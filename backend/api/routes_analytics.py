from flask import Blueprint, jsonify
import logging
from ..services.attendance_service import get_today_stats, get_summary, get_attendance_records
from ..utils.auth import token_required
from datetime import date, timedelta

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")
logger = logging.getLogger(__name__)

@analytics_bp.route("", methods=["GET"])
@token_required
def get_analytics():
    """Get comprehensive analytics data."""
    logger.info("Generating analytics report")
    try:
        # Get today's stats
        today_stats = get_today_stats()

        # Get overall summary
        summary = get_summary()

        # Calculate attendance percentage
        total_students = summary.get("total_students", 0)
        present_today = today_stats.get("present_today", 0)
        attendance_percentage = (present_today / total_students * 100) if total_students > 0 else 0

        # Get recent records (last 7 days)
        recent_records = []
        for i in range(7):
            check_date = date.today() - timedelta(days=i)
            records = get_attendance_records(check_date.isoformat())
            recent_records.extend(records)

        # Calculate weekly stats
        weekly_present = len(set(r.get("name") for r in recent_records if r.get("name")))

        analytics_data = {
            "total_students": total_students,
            "present_today": present_today,
            "late_students": today_stats.get("late_students", 0),
            "attendance_percentage": round(attendance_percentage, 2),
            "total_records": len(get_attendance_records()),
            "weekly_unique_attendees": weekly_present
        }
        
        logger.debug(f"Analytics data: {analytics_data}")
        return jsonify(analytics_data)
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate analytics"}), 500