from flask import Blueprint, jsonify, request
import logging

from ..services.student_service import StudentService
from ..utils.auth import token_required

students_bp = Blueprint("students", __name__, url_prefix="/api/students")
logger = logging.getLogger(__name__)


@students_bp.route("", methods=["GET"])
@token_required
def list_students():
    logger.info("Fetching student list")
    try:
        svc = StudentService()
        names = svc.list_students()
        logger.info(f"Retrieved {len(names)} students")
        return jsonify(names)
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve students"}), 500


@students_bp.route("", methods=["POST"])
@token_required
def add_student():
    logger.info("Adding new student")
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        logger.warning("Student addition failed: name field missing")
        return jsonify({"error": "name field is required"}), 400
    try:
        student = StudentService().add_student(name)
        logger.info(f"Student added successfully: {name}")
        return jsonify({"name": student}), 201
    except Exception as exc:
        logger.error(f"Error adding student {name}: {str(exc)}", exc_info=True)
        return jsonify({"error": str(exc)}), 500
