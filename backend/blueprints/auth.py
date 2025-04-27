from flask import Blueprint, jsonify, request, session, redirect
from services.auth_service import AuthService
from models.user import User
from config.settings import FRONTEND_URL, SCOPES
from config.database import Database
from utils.helpers import format_error_response
from utils.logger import auth_logger, log_error

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()

@auth_bp.route('/login')
def login():
    try:
        auth_logger.info("Login attempt initiated")
        # Log request headers and origin
        auth_logger.info(f"Request headers: {dict(request.headers)}")
        auth_logger.info(f"Request origin: {request.headers.get('Origin')}")
        auth_logger.info(f"Current session: {dict(session)}")
        
        authorization_url = auth_service.get_authorization_url()
        auth_logger.info("Generated authorization URL successfully")
        return jsonify({
            "authorization_url": authorization_url,
            "scope_info": {
                "required_scopes": SCOPES,
                "prompt": "consent"
            }
        })
    except Exception as e:
        error_message = str(e)
        auth_logger.error(f"Login error: {error_message}")
        session.clear()
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
        auth_logger.info(f"Session before logout: {dict(session)}")
        
        if user_id:
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
        auth_logger.info(f"Session after logout: {dict(session)}")
        return jsonify({"message": "Successfully logged out"})
    except Exception as e:
        log_error(auth_logger, e, f"Logout failed for user: {user_id}")
        return format_error_response(e, 500)

@auth_bp.route('/check')
def check_auth_status():
    """Check if the user is currently authenticated."""
    auth_logger.info(f"Auth check - Request headers: {dict(request.headers)}")
    auth_logger.info(f"Auth check - Request cookies: {dict(request.cookies)}")
    auth_logger.info(f"Auth check - Current session: {dict(session)}")
    
    user_id = session.get('user_id')
    auth_logger.info(f"Auth check initiated for user: {user_id}")
    
    is_authenticated = user_id is not None
    
    if is_authenticated:
        user = User.find_by_id(user_id)
        auth_logger.info(f"User found in database: {user is not None}")
        if not user or not user.get_credentials():
            is_authenticated = False
            session.clear()
            auth_logger.warning(f"Invalid session found for user_id: {user_id}. Session cleared.")
            auth_logger.info(f"Session after clearing: {dict(session)}")

    auth_logger.info(f"Auth check final status: {is_authenticated}")
    response = jsonify({"authenticated": is_authenticated})
    auth_logger.info(f"Response headers: {dict(response.headers)}")
    return response