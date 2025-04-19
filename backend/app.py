from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient # Import MongoClient

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey") # Replace with a strong secret key in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Or 'None' if frontend and backend are on different domains and using HTTPS

# Update CORS configuration to allow requests from both ports during transition
CORS(app, 
     supports_credentials=True, 
     origins=["http://localhost:3000", "http://localhost:3001"],
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

# --- Routes ---

@app.route('/')
def index():
    return "Backend is running!"

@app.route('/auth/google')
def auth_google():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        print(f"Error fetching token: {e}")
        # Handle specific exceptions like oauthlib.oauth2.rfc6749.errors.InvalidGrantError
        return jsonify({"error": "Failed to fetch token", "details": str(e)}), 400


    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # Redirect to the frontend summary page after successful login
    # Make sure your frontend is running on this port
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3001")
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

    if db is None: # Check if MongoDB connection is available
        return jsonify({"error": "Database connection failed"}), 500

    try:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])

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
        # You might want to store the user ID or some identifier along with the summary
        summary_collection = db['summaries'] # Select a collection
        summary_doc = {
            "user_id": session.get('user_id', 'unknown'), # Example: Get user ID if stored in session
            "summary_text": response.text,
            "generated_at": datetime.datetime.utcnow()
        }
        # summary_collection.insert_one(summary_doc) # Uncomment to actually store the data
        # print("Summary stored in MongoDB.")


        # --- Update session credentials if refreshed ---
        # google-auth automatically refreshes the token if necessary
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

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
    # Make sure to run with HTTPS if deploying or if frontend/backend are on different domains
    # For development, HTTP is usually fine if both are on localhost
    # Example using self-signed certs (pip install pyopenssl):
    # context = ('adhoc') # Creates cert.pem and key.pem
    # app.run(debug=True, ssl_context=context, port=5000)
    app.run(debug=True, port=5000) # Run on HTTP for local development
