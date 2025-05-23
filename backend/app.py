from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
import ssl
import atexit

from config.settings import (
    FLASK_SECRET_KEY,
    CORS_ORIGINS,
    CORS_HEADERS,
    CORS_METHODS,
    FRONTEND_URL
)
from config.database import Database
from services.auth_service import AuthService
from services.scheduler_service import SchedulerService
from models.user import User
from utils.helpers import format_error_response
from utils.logger import auth_logger, log_error

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Configure session cookie settings
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allow cross-origin cookies
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)

# Configure CORS
CORS(app, 
     origins=CORS_ORIGINS,
     allow_headers=CORS_HEADERS,
     methods=CORS_METHODS,
     supports_credentials=True)

# Initialize database and ensure connection
db = Database.get_instance()
if not db.ensure_connected():
    print("Warning: Failed to establish database connection. Some features may not work.")

# Initialize services
auth_service = AuthService()
scheduler_service = SchedulerService.get_instance()

# Start the scheduler
scheduler_service.start()

# Register scheduler shutdown on app exit
atexit.register(scheduler_service.stop)

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback at root level"""
    try:
        auth_logger.info("OAuth callback initiated")
        auth_logger.info(f"Request headers: {dict(request.headers)}")
        
        code = request.args.get('code')
        if not code:
            auth_logger.error("No authorization code received in callback")
            return format_error_response("No authorization code received", 400)

        error = request.args.get('error')
        if error:
            auth_logger.error(f"OAuth error received: {error}")
            if error == 'access_denied':
                return format_error_response("Access denied by user", 403)
            return format_error_response(f"Authorization error: {error}", 400)

        # Ensure database is connected
        if not db.ensure_connected():
            auth_logger.error("Database connection failed during OAuth callback")
            return format_error_response("Database service unavailable", 503)

        # Exchange authorization code for tokens
        try:
            token = auth_service.get_token(request.url, request.base_url)
            if not token:
                auth_logger.error("Failed to obtain access token")
                return format_error_response("Failed to obtain access token", 500)
        except Exception as e:
            log_error(auth_logger, e, "Token exchange failed")
            return format_error_response(str(e), 500)

        # Get user info
        try:
            user_info = auth_service.get_user_info()
            if not user_info:
                auth_logger.error("Failed to get user info")
                return format_error_response("Failed to get user info", 500)
                
            # Validate required fields
            required_fields = ['sub', 'email']
            missing_fields = [field for field in required_fields if field not in user_info]
            if missing_fields:
                auth_logger.error(f"Missing required user info fields: {missing_fields}")
                auth_logger.error(f"User info received: {user_info}")
                return format_error_response("Incomplete user information received from Google", 500)

            user = User(user_info['sub'], user_info['email'], user_info.get('name', ''))
            user.save_credentials(token)
            session['user_id'] = user_info['sub']
            session.modified = True
            
            auth_logger.info(f"User authenticated: {session['user_id']}")
            return redirect(FRONTEND_URL)
            
        except Exception as e:
            log_error(auth_logger, e, "Failed to save user")
            return format_error_response(str(e), 500)

    except Exception as e:
        log_error(auth_logger, e, "OAuth callback failed")
        return format_error_response(str(e), 500)

# Import blueprints after database initialization
from blueprints.auth import auth_bp
from blueprints.summary import summary_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')  # auth_bp now includes the /auth prefix
app.register_blueprint(summary_bp)

@app.route('/')
def index():
    if not db.is_connected():
        return jsonify({
            "status": "degraded",
            "message": "Database connection unavailable"
        }), 503
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('../frontend/cert.pem', '../frontend/key.pem')
    app.run(host='0.0.0.0', port=5000, ssl_context=context, debug=True)
