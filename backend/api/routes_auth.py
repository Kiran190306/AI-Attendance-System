from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
import logging
from ..services.user_service import authenticate_user, create_user, create_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login endpoint that returns a JWT token."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        logger.warning(f"Login attempt with missing credentials from {request.remote_addr}")
        return jsonify({"error": "Username and password are required"}), 400

    logger.info(f"Login attempt for user: {username}")
    
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"Failed login attempt for user: {username} from {request.remote_addr}")
        return jsonify({"error": "Invalid credentials"}), 401

    try:
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        logger.info(f"Successful login for user: {username}")
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
    except Exception as e:
        logger.error(f"Error generating token for user {username}: {str(e)}", exc_info=True)
        return jsonify({"error": "Token generation failed"}), 500

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register endpoint for creating new users."""
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        logger.warning(f"Register attempt with missing credentials from {request.remote_addr}")
        return jsonify({"error": "Username, email, and password are required"}), 400

    logger.info(f"Register attempt for user: {username}, email: {email}")

    try:
        user = create_user(username, email, password)
        access_token = create_access_token(data={"sub": user.username})
        logger.info(f"New user created successfully: {username}")
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 201
    except IntegrityError:
        logger.warning(f"User create conflict for {username}")
        return jsonify({"error": "Username or email already exists"}), 409
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}", exc_info=True)
        return jsonify({"error": "User creation failed", "details": str(e)}), 400

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Signup endpoint for creating new users."""
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        logger.warning(f"Signup attempt with missing credentials from {request.remote_addr}")
        return jsonify({"error": "Username, email, and password are required"}), 400

    logger.info(f"Signup attempt for user: {username}, email: {email}")

    try:
        user = create_user(username, email, password)
        # Create access token for the new user
        access_token = create_access_token(data={"sub": user.username})
        logger.info(f"New user created successfully: {username}")
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}", exc_info=True)
        return jsonify({"error": "User creation failed", "details": str(e)}), 400