from flask import Blueprint, jsonify, request
import base64
import io
from datetime import datetime
from ..core.face_engine import FaceRecognitionEngine
from ..core.attendance_service import AttendanceService

mobile_bp = Blueprint("mobile", __name__, url_prefix="/api/mobile")

# lazy singletons
_engine: FaceRecognitionEngine | None = None
_att_service: AttendanceService | None = None


def get_engine() -> FaceRecognitionEngine:
    global _engine
    if _engine is None:
        _engine = FaceRecognitionEngine()
        _engine.initialize()
    return _engine


def get_att_service() -> AttendanceService:
    global _att_service
    if _att_service is None:
        _att_service = AttendanceService()
    return _att_service


def _decode_image(image_data: str):
    # expect data url or base64
    if image_data.startswith('data:'):
        image_data = image_data.split(',', 1)[1]
    return base64.b64decode(image_data)


@mobile_bp.route('/status', methods=['GET'])
def mobile_status():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


@mobile_bp.route('/students', methods=['GET'])
def mobile_students():
    # simply list enrolled names
    names = get_engine()._name_list if hasattr(get_engine(), '_name_list') else []
    return jsonify({'students': names})


@mobile_bp.route('/attendance', methods=['POST'])
def mobile_attendance():
    data = request.get_json() or {}
    device = data.get('device_id')
    token = data.get('device_token')
    image_data = data.get('image_data')
    if not device or not token or not image_data:
        return jsonify({'error': 'device_id, device_token and image_data required'}), 400
    # TODO: verify token (stubbed)
    # decode and run recognition
    img_bytes = _decode_image(image_data)
    engine = get_engine()
    import numpy as np, cv2
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({'error': 'invalid image'}), 400
    results, _ = engine.process_frame(frame)
    if not results:
        return jsonify({'status': 'no_face'}), 200
    face = results[0]
    name = face.get('name')
    conf = face.get('confidence', 0.0)
    if not name:
        return jsonify({'status': 'unrecognized'}), 200
    # mark attendance; duplicate prevention inside service
    att = get_att_service()
    marked = att.mark(name, confidence=conf)
    # log mobile event
    with open('logs/mobile_attendance.log', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()},device={device},name={name},conf={conf},marked={marked}\n")
    status = 'attendance_marked' if marked else 'duplicate'
    return jsonify({'status': status, 'student': name, 'time': datetime.now().strftime('%H:%M:%S')})
