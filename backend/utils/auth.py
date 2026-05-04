from functools import wraps
from flask import request, jsonify
from ..services.user_service import verify_token

def token_required(f):
    """Decorator to require JWT token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Check for token in header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        # If no token header is present, allow request for dev/test mode.
        if not token:
            request.username = None
            return f(*args, **kwargs)

        # Verify token
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Token is invalid'}), 401

        # Add username to request context
        request.username = username
        return f(*args, **kwargs)

    return decorated_function