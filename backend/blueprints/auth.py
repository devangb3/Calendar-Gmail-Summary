from flask import Blueprint, jsonify, request, session, redirect
from services.auth_service import AuthService
from models.user import User
from config.settings import FRONTEND_URL, SCOPES  # Add SCOPES import
from config.database import Database
from utils.helpers import format_error_response
from utils.logger import auth_logger, log_error

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')  # Add url_prefix
auth_service = AuthService()

@auth_bp.route('/login')
def login():
    try:
        auth_logger.info("Login attempt initiated")
        authorization_url = auth_service.get_authorization_url()
        auth_logger.info("Generated authorization URL successfully")
        return jsonify({
            "authorization_url": authorization_url,
            "scope_info": {
                "required_scopes": SCOPES,
                "prompt": "consent"  # Indicates we're forcing consent screen
            }
        })
    except Exception as e:
        error_message = str(e)
        auth_logger.error(f"Login error: {error_message}")
        session.clear()  # Clear session on any error
        return format_error_response({
            "error": "Authentication error",
            "message": error_message,
            "action": "Please try logging in again to grant the required permissions."
        }, 500)

@auth_bp.route('/logout')
def logout():
    try:
        user_id = session.get('user_id')
        auth_logger.info(f"Logout initiated for user: {user_id}")
        if user_id:
            # Ensure database is connected before proceeding
            db = Database.get_instance()
            if db is None or not db.ensure_connected():
                auth_logger.error("Database connection failed during logout")
                return format_error_response("Database service unavailable", 503)

            user = User.find_by_id(user_id)
            if user:
                user.remove_credentials()
                auth_logger.info(f"Credentials removed for user: {user_id}")
        session.clear()
        auth_logger.info(f"Logout successful for user: {user_id}")
        return jsonify({"message": "Successfully logged out"})
    except Exception as e:
        log_error(auth_logger, e, f"Logout failed for user: {user_id}")
        return format_error_response(e, 500)

@auth_bp.route('/check')
def check_auth_status():
    """Check if the user is currently authenticated."""
    user_id = session.get('user_id')
    is_authenticated = user_id is not None
    auth_logger.info(f"Auth check initiated for user: {user_id}")
    if is_authenticated:
        # Optionally, verify the user still exists and credentials are valid
        user = User.find_by_id(user_id)
        if not user or not user.get_credentials():
            is_authenticated = False
            session.clear()  # Clear session if user/credentials invalid
            auth_logger.warning(f"Invalid session found for user_id: {user_id}. Session cleared.")

    auth_logger.debug(f"Auth check status for session: {is_authenticated}")
    return jsonify({"authenticated": is_authenticated})