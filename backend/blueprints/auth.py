from flask import Blueprint, jsonify, request, session, redirect
from services.auth_service import AuthService
from models.user import User
from config.settings import FRONTEND_URL
from config.database import Database
from utils.helpers import format_error_response

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/login')
def login():
    try:
        authorization_url = auth_service.get_authorization_url()
        return jsonify({"authorization_url": authorization_url})
    except Exception as e:
        error_message = str(e)
        if 'scope' in error_message.lower():
            # Handle scope-related errors by forcing re-authentication
            session.clear()
            return jsonify({
                "error": "Authentication scope has changed. Please sign in again.",
                "authorization_url": auth_service.get_authorization_url()
            })
        return format_error_response(e, 500)

@auth_bp.route('/oauth2callback')
def oauth2callback():
    try:
        code = request.args.get('code')
        if not code:
            return format_error_response("No authorization code received", 400)

        error = request.args.get('error')
        if error:
            if error == 'access_denied':
                return format_error_response("Access denied by user", 403)
            return format_error_response(f"Authorization error: {error}", 400)

        # Ensure database is connected before proceeding
        db = Database.get_instance()
        if db is None or not db.ensure_connected():
            return format_error_response("Database service unavailable", 503)

        # Exchange authorization code for tokens
        try:
            print("[DEBUG] Exchanging authorization code for tokens")
            token = auth_service.get_token(request.url, request.base_url)
            if not token:
                return format_error_response("Failed to obtain access token", 500)
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Token exchange failed: {error_message}")
            if 'scope' in error_message.lower():
                session.clear()
                return redirect('/login')
            return format_error_response(f"Token exchange failed: {error_message}", 500)

        # Get user info with the new token
        print("[DEBUG] Fetching user info with new token")
        user_info = auth_service.get_user_info()
        if not user_info:
            return format_error_response("Failed to get user info from Google. Please try again.", 500)
        
        # Create and save user
        try:
            user = User(user_info['sub'], user_info['email'], user_info.get('name', ''))
            user.save_credentials(token)
            session['user_id'] = user_info['sub']
            print(f"[DEBUG] User credentials saved successfully for ID: {user_info['sub']}")
            
            # Directly redirect to frontend URL
            return redirect(FRONTEND_URL)
        except Exception as e:
            print(f"[ERROR] Failed to save user credentials: {str(e)}")
            return format_error_response(f"Failed to save user credentials: {str(e)}", 500)
    except Exception as e:
        print(f"[ERROR] Unexpected error in oauth2callback: {str(e)}")
        return format_error_response(e, 500)

@auth_bp.route('/logout')
def logout():
    try:
        user_id = session.get('user_id')
        if user_id:
            # Ensure database is connected before proceeding
            db = Database.get_instance()
            if db is None or not db.ensure_connected():
                return format_error_response("Database service unavailable", 503)

            user = User.find_by_id(user_id)
            if user:
                user.remove_credentials()
        session.clear()
        return jsonify({"message": "Successfully logged out"})
    except Exception as e:
        return format_error_response(e, 500)