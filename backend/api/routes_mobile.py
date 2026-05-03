from flask import Blueprint, jsonify, request
import base64
import io
import logging
from datetime import datetime
from ..core.face_engine import FaceRecognitionEngine
from ..core.attendance_service import AttendanceService
from ..utils.auth import token_required

mobile_bp = Blueprint("mobile", __name__, url_prefix="/api/mobile")
logger = logging.getLogger(__name__)

# lazy singletons
_engine: FaceRecognitionEngine | None = None
_att_service: AttendanceService | None = None


def get_engine() -> FaceRecognitionEngine:
    global _engine
    if _engine is None:
        logger.info("Initializing face recognition engine")
        _engine = FaceRecognitionEngine()
        _engine.initialize()
    return _engine


def get_att_service() -> AttendanceService:
    global _att_service
    if _att_service is None:
        logger.info("Initializing attendance service")
        _att_service = AttendanceService()
    return _att_service


def _decode_image(image_data: str):
    # expect data url or base64
    if image_data.startswith('data:'):
        image_data = image_data.split(',', 1)[1]
    return base64.b64decode(image_data)


@mobile_bp.route('/status', methods=['GET'])
@token_required
def mobile_status():
    logger.debug("Mobile status check")
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


@mobile_bp.route('/students', methods=['GET'])
@token_required
def mobile_students():
    logger.info("Fetching mobile students list")
    try:
        # simply list enrolled names
        names = get_engine()._name_list if hasattr(get_engine(), '_name_list') else []
        logger.info(f"Found {len(names)} students for mobile")
        return jsonify({'students': names})
    except Exception as e:
        logger.error(f"Error fetching mobile students: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve students'}), 500


@mobile_bp.route('/attendance', methods=['POST'])
@token_required
def mobile_attendance():
    logger.info("Mobile attendance submission received")
    data = request.get_json() or {}
    device = data.get('device_id')
    image_data = data.get('image_data')
    if not device or not image_data:
        logger.warning(f"Invalid mobile attendance request - missing device_id or image_data from {request.remote_addr}")
        return jsonify({'error': 'device_id and image_data required'}), 400
    
    try:
        # decode and run recognition
        img_bytes = _decode_image(image_data)
        engine = get_engine()
        import numpy as np, cv2
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            logger.warning(f"Invalid image data from device: {device}")
            return jsonify({'error': 'invalid image'}), 400
        
        logger.debug(f"Processing face recognition for device: {device}")
        results, _ = engine.process_frame(frame)
        if not results:
            logger.info(f"No face detected from device: {device}")
            return jsonify({'status': 'no_face'}), 200
        
        face = results[0]
        name = face.get('name')
        conf = face.get('confidence', 0.0)
        if not name:
            logger.info(f"Unrecognized face from device: {device}")
            return jsonify({'status': 'unrecognized'}), 200
        
        # mark attendance; duplicate prevention inside service
        att = get_att_service()
        marked = att.mark(name, confidence=conf)
        
        if marked:
            logger.info(f"Attendance marked for {name} from device {device} (confidence: {conf:.2f})")
        else:
            logger.info(f"Duplicate attendance attempt for {name} from device {device}")
        
        status = 'attendance_marked' if marked else 'duplicate'
        return jsonify({'status': status, 'student': name, 'time': datetime.now().strftime('%H:%M:%S')})
    
    except Exception as e:
        logger.error(f"Error processing mobile attendance: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to process attendance'}), 500
