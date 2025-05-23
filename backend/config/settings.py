import os
from dotenv import load_dotenv
from utils.logger import auth_logger

load_dotenv()

# Flask Configuration
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://localhost:3001")
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://localhost:5000')

auth_logger.info(f"Frontend URL configured as: {FRONTEND_URL}")
auth_logger.info(f"Backend URL configured as: {BACKEND_URL}")
auth_logger.info(f"OAuth redirect URI configured as: {os.getenv('OAUTH_REDIRECT_URI', 'https://localhost:5000/oauth2callback')}")

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = 'calendar_summary_db'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "https://localhost:5000/oauth2callback"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
CLIENT_SECRETS_FILE = "client_secret.json"

# Google API Scopes
SCOPES = [
    'openid',  # Required for user ID
    'https://www.googleapis.com/auth/userinfo.profile',  # Required for user profile
    'https://www.googleapis.com/auth/userinfo.email',  # Required for email
    'https://www.googleapis.com/auth/calendar.readonly',  # For reading calendar events
    'https://www.googleapis.com/auth/calendar',  # Full calendar access for reading and writing
    'https://www.googleapis.com/auth/gmail.readonly',  # For reading gmail
    'https://www.googleapis.com/auth/gmail.send',  # For sending emails
]

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = 'models/gemini-2.0-flash'

# CORS Configuration
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "https://localhost:3001", "https://calendar-gmail-summary-frontend.onrender.com"]
CORS_HEADERS = ["Content-Type", "Authorization"]
CORS_METHODS = ["GET", "POST", "OPTIONS"]

auth_logger.info(f"CORS Origins: {CORS_ORIGINS}")