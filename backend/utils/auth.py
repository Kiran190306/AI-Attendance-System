from functools import wraps
from flask import request

def token_required(f):
    """No-op auth decorator. Auth bypass active."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Auth bypass active")
        request.username = None
        return f(*args, **kwargs)

    return decorated_function