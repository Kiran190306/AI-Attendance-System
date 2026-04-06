from flask import Blueprint, jsonify, request

from ..services.student_service import StudentService

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


@students_bp.route("", methods=["GET"])
def list_students():
    svc = StudentService()
    names = svc.list_students()
    return jsonify(names)


@students_bp.route("", methods=["POST"])
def add_student():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name field is required"}), 400
    try:
        student = StudentService().add_student(name)
        return jsonify({"name": student}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
