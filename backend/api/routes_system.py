from flask import Blueprint, jsonify
import logging

from ..core.dataset_loader import DatasetLoader
from ..utils.auth import token_required

system_bp = Blueprint("system", __name__, url_prefix="/api/system")
logger = logging.getLogger(__name__)


@system_bp.route("/status", methods=["GET"])
@token_required
def status():
    logger.info("Checking system status")
    try:
        loader = DatasetLoader()
        stats = loader.get_statistics()
        logger.info(f"System status OK. Dataset stats: {stats}")
        return jsonify({"dataset": stats, "status": "ok"})
    except Exception as e:
        logger.error(f"Error retrieving system status: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve system status"}), 500
