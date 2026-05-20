"""
Training API Routes
Handles student enrollment and model training
"""

from flask import Blueprint, jsonify, request
import logging
import base64
import io
from PIL import Image
from ..core.face_trainer import get_trainer

training_bp = Blueprint("training", __name__, url_prefix="/api/training")
logger = logging.getLogger(__name__)


@training_bp.route("/add_student", methods=["POST"], strict_slashes=False)
def add_student():
    """Add a new student with face image"""
    logger.info("POST /api/training/add_student received")
    
    try:
        # Get form data
        student_name = request.form.get('name')
        
        if not student_name:
            return jsonify({"error": "Student name is required"}), 400
        
        # Check for file upload
        if 'image' not in request.files:
            # Try to get base64 from JSON
            data = request.get_json()
            if not data or 'image' not in data:
                return jsonify({"error": "Image is required"}), 400
            
            # Decode base64
            try:
                image_base64 = data['image']
                # Remove data URL prefix if present
                if image_base64.startswith('data:image'):
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
            except Exception as e:
                logger.error(f"Error decoding base64: {e}")
                return jsonify({"error": "Invalid image data"}), 400
        else:
            # Get file upload
            file = request.files['image']
            image_data = file.read()
        
        # Validate image
        try:
            image = Image.open(io.BytesIO(image_data))
            # Ensure RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return jsonify({"error": "Invalid image file"}), 400
        
        # Add student using trainer
        trainer = get_trainer()
        success = trainer.add_student(student_name, image_data)
        
        if success:
            logger.info(f"Successfully added student: {student_name}")
            return jsonify({
                "success": True,
                "message": f"Student '{student_name}' added successfully",
                "student_name": student_name
            }), 200
        else:
            return jsonify({"error": "Failed to add student"}), 500
            
    except Exception as e:
        logger.error(f"Error adding student: {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500


@training_bp.route("/train", methods=["POST"], strict_slashes=False)
def train_model():
    """Retrain model from dataset"""
    logger.info("POST /api/training/train received")
    
    try:
        trainer = get_trainer()
        stats = trainer.train_from_dataset()
        
        logger.info(f"Training complete: {stats}")
        return jsonify({
            "success": True,
            "message": "Model retrained successfully",
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        return jsonify({"error": "Failed to train model"}), 500


@training_bp.route("/students", methods=["GET"], strict_slashes=False)
def get_students():
    """Get list of trained students"""
    logger.info("GET /api/training/students received")
    
    try:
        trainer = get_trainer()
        students = trainer.get_students()
        
        return jsonify({
            "success": True,
            "students": students,
            "total": len(students)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting students: {e}", exc_info=True)
        return jsonify({"error": "Failed to get students"}), 500


@training_bp.route("/stats", methods=["GET"], strict_slashes=False)
def get_stats():
    """Get training statistics"""
    logger.info("GET /api/training/stats received")
    
    try:
        trainer = get_trainer()
        stats = trainer.get_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to get stats"}), 500
