from functools import wraps
from flask import request, jsonify
from ..services.user_service import verify_token

def token_required(f):
    """Require a valid JWT token for protected API routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "") or ""
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            payload = request.get_json(silent=True) or {}
            token = request.args.get("token") or payload.get("token")

        if not token:
            return jsonify({"error": "Authorization token missing"}), 401

        username = verify_token(token)
        if not username:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.username = username
        return f(*args, **kwargs)

    return decorated_function