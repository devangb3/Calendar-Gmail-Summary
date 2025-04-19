from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient # Import MongoClient
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from oauthlib.oauth2 import WebApplicationClient
import requests

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey") # Replace with a strong secret key in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Or 'None' if frontend and backend are on different domains and using HTTPS

# Update CORS configuration to allow requests from both ports during transition
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:3000", "http://localhost:3001", "https://localhost:3001"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# --- MongoDB Configuration ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/") # Default to local MongoDB
print(f"Attempting to connect to MongoDB with URI: {MONGO_URI}") # <-- Add logging here
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client['calendar_summary_db'] # Select your database
    # You can test the connection here if needed, e.g., by listing collections
    mongo_client.server_info() # Raises an exception if connection fails
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo_client = None
    db = None

# --- OAuth Configuration ---
CLIENT_SECRETS_FILE = "client_secret.json" # Download this from Google Cloud Console
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'
]
API_SERVICE_NAME = 'your_api_service_name' # Not directly used here but good practice
API_VERSION = 'v1' # Not directly used here but good practice

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17') # Or choose another appropriate model
else:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
    model = None

# --- Google OAuth Configuration ---
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'  # Require HTTPS
# Load client ID and secret from environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "https://localhost:5000/oauth2callback"

# Check if credentials are loaded
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment variables.")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Add these constants after your imports
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_google_provider_cfg():
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch Google provider config: {e}")
        return None

# --- Helper Functions ---
def credentials_to_dict(credentials):
    """Convert Google OAuth2 credentials to a dictionary format"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'scopes': credentials.scopes
    }

# --- Routes ---

@app.route('/')
def index():
    return "Backend is running!"

@app.route("/auth/google")
def google_auth():
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return "Error: Failed to fetch Google provider configuration", 500

    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login with all required scopes
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="https://localhost:5000/oauth2callback",
        scope=[
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/gmail.readonly"
        ],
        access_type="offline",  # Request a refresh token
        prompt="consent"  # Force consent screen to ensure getting refresh token
    )
    return redirect(request_uri)

@app.route('/oauth2callback')
def oauth2callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return "Error: Failed to fetch Google provider configuration", 500
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    try:
        client.parse_request_body_response(token_response.text)
    except Exception as e:
        print(f"Error parsing token response: {e}")
        print(f"Response status: {token_response.status_code}")
        print(f"Response text: {token_response.text}")
        return jsonify({"error": "Failed to parse token response", "details": str(e)}), 400

    # Now that we have tokens, let's find and store user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    user_info = userinfo_response.json()

    if userinfo_response.status_code != 200:
        return jsonify({"error": "Failed to fetch user info"}), 500

    # Create credentials object
    credentials = google.oauth2.credentials.Credentials(
        token=client.token['access_token'],
        refresh_token=client.token.get('refresh_token'),
        token_uri=google_provider_cfg['token_endpoint'],
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=[
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/gmail.readonly',
            'openid',
            'email',
            'profile'
        ]
    )

    # Store credentials and user info in session
    session['credentials'] = credentials_to_dict(credentials)
    session['user_id'] = user_info.get("sub")
    session['user_email'] = user_info.get("email")
    session['user_name'] = user_info.get("name")

    # Redirect to frontend
    frontend_url = os.environ.get("FRONTEND_URL", "https://localhost:3001")
    return redirect(f"{frontend_url}/summary")

@app.route('/api/check_auth')
def check_auth():
    if 'credentials' not in session:
        return jsonify({"isAuthenticated": False})
    # You might want to add logic here to check if the token is still valid
    # or refresh it if necessary.
    return jsonify({"isAuthenticated": True})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('credentials', None)
    return jsonify({"message": "Logged out successfully"})


@app.route('/api/summary')
def get_summary():
    if 'credentials' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    if not model:
        return jsonify({"error": "Gemini API not configured"}), 500

    if db is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Create credentials from session data
        credentials = google.oauth2.credentials.Credentials(
            **session['credentials']
        )

        # Check if the token needs refreshing
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(google.auth.transport.requests.Request())
                session['credentials'] = credentials_to_dict(credentials)
            except Exception as e:
                print(f"Error refreshing token: {e}")
                session.clear()
                return jsonify({"error": "Failed to refresh token, please log in again"}), 401

        # --- Fetch Calendar Events ---
        calendar_service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        # Example: Get events for the next 7 days
        import datetime
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'

        print('Getting the upcoming 10 events')
        events_result = calendar_service.events().list(calendarId='primary', timeMin=now,
                                                      maxResults=10, singleEvents=True,
                                                      orderBy='startTime', timeMax=time_max).execute()
        calendar_events = events_result.get('items', [])
        calendar_prompt_text = "Summarize the following upcoming calendar events:\n"
        if not calendar_events:
            calendar_prompt_text += "No upcoming events found."
        else:
            for event in calendar_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                calendar_prompt_text += f"- {start}: {event['summary']}\n"


        # --- Fetch Gmail Messages ---
        gmail_service = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)
        # Example: Get recent unread emails (adjust query as needed)
        results = gmail_service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=5).execute()
        messages = results.get('messages', [])

        gmail_prompt_text = "Summarize the following recent unread emails:\n"
        if not messages:
            gmail_prompt_text += "No recent unread emails found."
        else:
            for message_info in messages:
                msg = gmail_service.users().messages().get(userId='me', id=message_info['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                gmail_prompt_text += f"- From: {sender}, Subject: {subject}\n"


        # --- Generate Summary with Gemini ---
        full_prompt = f"{calendar_prompt_text}\n\n{gmail_prompt_text}"

        print("\n--- Sending Prompt to Gemini ---")
        print(full_prompt)
        print("------------------------------\n")

        response = model.generate_content(full_prompt)

        print("\n--- Received Response from Gemini ---")
        print(response.text)
        print("-----------------------------------\n")

        # --- Store summary in MongoDB (Example) ---
        summary_collection = db['summaries'] # Select a collection
        summary_doc = {
            "user_id": session.get('user_id', 'unknown'), # Use user_id from session
            "summary_text": response.text,
            "generated_at": datetime.datetime.utcnow()
        }
        # summary_collection.insert_one(summary_doc) # Uncomment to actually store the data
        # print("Summary stored in MongoDB.")


        return jsonify({
            "summary": response.text,
            "calendarLink": "https://calendar.google.com/",
            "gmailLink": "https://mail.google.com/"
        })

    except Exception as e:
        print(f"Error fetching data or generating summary: {e}")
        # Consider more specific error handling
        return jsonify({"error": "Failed to get summary", "details": str(e)}), 500


if __name__ == '__main__':
    # Enable HTTPS for development
    app.wsgi_app = ProxyFix(app.wsgi_app)
    run_simple('localhost', 
               5000, 
               app,
               ssl_context='adhoc',  # This creates a self-signed certificate
               use_reloader=True)
