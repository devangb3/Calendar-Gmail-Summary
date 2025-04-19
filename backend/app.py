from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from oauthlib.oauth2 import WebApplicationClient
import requests
import datetime
from datetime import timedelta

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
print(f"Attempting to connect to MongoDB with URI: {MONGO_URI}")
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client['calendar_summary_db'] # Select your database
    users_collection = db['users'] # Collection for user data
    summaries_collection = db['summaries'] # Collection for cached summaries
    # Create index on user_id for faster lookups
    users_collection.create_index("user_id", unique=True)
    summaries_collection.create_index([("user_id", 1), ("generated_at", -1)]) # Index for summary lookup
    mongo_client.server_info() # Raises an exception if connection fails
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo_client = None
    db = None
    users_collection = None
    summaries_collection = None

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

    # --- Store/Update User in MongoDB ---
    user_id = user_info.get("sub")
    user_email = user_info.get("email")
    user_name = user_info.get("name")
    credentials_dict = credentials_to_dict(credentials)

    if db is not None and users_collection is not None:
        try:
            users_collection.update_one(
                {'user_id': user_id},
                {'$set': {
                    'email': user_email,
                    'name': user_name,
                    'credentials': credentials_dict,
                    'updated_at': datetime.datetime.utcnow()
                },
                 '$setOnInsert': {'created_at': datetime.datetime.utcnow()}}, # Set created_at only on insert
                upsert=True # Insert if not found, update if found
            )
            print(f"User {user_id} data stored/updated in MongoDB.")
        except Exception as e:
            print(f"Error storing/updating user data in MongoDB: {e}")

    # Store only user_id in session
    session['user_id'] = user_id
    # Clear old credentials from session if they exist
    session.pop('credentials', None)
    session.pop('user_email', None)
    session.pop('user_name', None)

    # Redirect to frontend
    frontend_url = os.environ.get("FRONTEND_URL", "https://localhost:3001")
    return redirect(f"{frontend_url}/summary")

@app.route('/api/check_auth')
def check_auth():
    # Check for user_id in session
    if 'user_id' not in session:
        return jsonify({"isAuthenticated": False})
    # Optionally, you could check if the user_id still exists in the DB
    return jsonify({"isAuthenticated": True})


@app.route('/api/logout', methods=['POST'])
def logout():
    # Clear user_id from session
    session.pop('user_id', None)
    # Clear other potential session data if needed
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.route('/api/summary')
def get_summary():
    # Check if user is logged in via session
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    user_id = session['user_id']

    if not model:
        return jsonify({"error": "Gemini API not configured"}), 500

    if db is None or users_collection is None or summaries_collection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # --- Check for Cached Summary ---
        one_hour_ago = datetime.datetime.utcnow() - timedelta(hours=1)
        cached_summary = summaries_collection.find_one(
            {'user_id': user_id, 'generated_at': {'$gte': one_hour_ago}},
            sort=[('generated_at', -1)] # Get the most recent one within the hour
        )

        if cached_summary:
            print(f"Returning cached summary for user {user_id}")
            return jsonify({
                "summary": cached_summary['summary_text'],
                "calendarLink": "https://calendar.google.com/",
                "gmailLink": "https://mail.google.com/",
                "cached": True, # Indicate that this is a cached response
                "generated_at": cached_summary['generated_at']
            })

        # --- No Cache Found or Cache Expired - Fetch User Credentials ---
        print(f"No recent cache found for user {user_id}. Generating new summary.")
        user_data = users_collection.find_one({'user_id': user_id})

        if not user_data or 'credentials' not in user_data:
            print(f"No credentials found for user {user_id} in DB.")
            session.clear() # Clear session as user data is missing
            return jsonify({"error": "User credentials not found, please log in again"}), 401

        # Create credentials from stored data
        credentials = google.oauth2.credentials.Credentials(
            **user_data['credentials']
        )

        # Check if the token needs refreshing
        token_refreshed = False
        if credentials.expired and credentials.refresh_token:
            try:
                print(f"Refreshing token for user {user_id}")
                credentials.refresh(google.auth.transport.requests.Request())
                # --- Update Refreshed Credentials in MongoDB ---
                new_credentials_dict = credentials_to_dict(credentials)
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'credentials': new_credentials_dict, 'updated_at': datetime.datetime.utcnow()}}
                )
                token_refreshed = True
                print(f"Token refreshed and updated in DB for user {user_id}")
            except Exception as e:
                print(f"Error refreshing token for user {user_id}: {e}")
                # If refresh fails, clear session and force re-login
                session.clear()
                # Optionally remove the invalid credentials from DB or mark them as invalid
                users_collection.update_one({'user_id': user_id}, {'$unset': {'credentials': ""}})
                return jsonify({"error": "Failed to refresh token, please log in again"}), 401

        # --- Fetch Calendar Events ---
        calendar_service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        import datetime as dt # Use alias to avoid conflict with module name
        now = dt.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        time_max = (dt.datetime.utcnow() + dt.timedelta(days=7)).isoformat() + 'Z'

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
        summary_text = response.text # Store the generated text

        print("\n--- Received Response from Gemini ---")
        print(summary_text)
        print("-----------------------------------\n")

        # --- Store New Summary in MongoDB Cache ---
        current_time = datetime.datetime.utcnow()
        summary_doc = {
            "user_id": user_id,
            "summary_text": summary_text,
            "generated_at": current_time,
            "prompt_used": full_prompt # Optionally store the prompt
        }
        # Insert the new summary
        summaries_collection.insert_one(summary_doc)
        print(f"New summary for user {user_id} stored in MongoDB cache.")


        return jsonify({
            "summary": summary_text,
            "calendarLink": "https://calendar.google.com/",
            "gmailLink": "https://mail.google.com/",
            "cached": False, # Indicate this is a newly generated response
            "generated_at": current_time
        })

    except google.auth.exceptions.RefreshError as re:
        print(f"Credentials refresh error for user {user_id}: {re}")
        session.clear()
        users_collection.update_one({'user_id': user_id}, {'$unset': {'credentials': ""}})
        return jsonify({"error": "Authentication expired or invalid, please log in again"}), 401
    except Exception as e:
        print(f"Error fetching data or generating summary for user {user_id}: {e}")
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
