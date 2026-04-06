from flask import Blueprint, jsonify

from ..core.dataset_loader import DatasetLoader

system_bp = Blueprint("system", __name__, url_prefix="/api/system")


@system_bp.route("/status", methods=["GET"])
def status():
    loader = DatasetLoader()
    stats = loader.get_statistics()
    return jsonify({"dataset": stats, "status": "ok"})
