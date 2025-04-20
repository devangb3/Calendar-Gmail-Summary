import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    CLIENT_SECRETS_FILE,
    SCOPES
)

class AuthService:
    def __init__(self):
        self.flow = None

    def get_authorization_url(self):
        """Generate the authorization URL for Google OAuth."""
        self.flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        # Always request a new token with consent to handle scope changes
        authorization_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url

    def get_token(self, authorization_response, base_url):
        """Exchange authorization code for tokens."""
        try:
            self.flow.fetch_token(
                authorization_response=authorization_response,
                authorization_base_url=base_url
            )
            
            # Ensure all required scopes are granted
            granted_scopes = set(self.flow.credentials.scopes)
            required_scopes = set(SCOPES)
            
            if not required_scopes.issubset(granted_scopes):
                missing_scopes = required_scopes - granted_scopes
                raise Exception(f"Missing required scopes: {', '.join(missing_scopes)}")
            
            return {
                'token': self.flow.credentials.token,
                'refresh_token': self.flow.credentials.refresh_token,
                'token_uri': self.flow.credentials.token_uri,
                'client_id': self.flow.credentials.client_id,
                'client_secret': self.flow.credentials.client_secret,
                'scopes': list(granted_scopes)  # Convert to list for JSON serialization
            }
        except Exception as e:
            print(f"Error fetching token: {e}")
            raise

    def get_user_info(self):
        """Get user information from Google."""
        try:
            if not self.flow or not self.flow.credentials:
                print("[ERROR] No valid OAuth flow or credentials available")
                return None
                
            credentials = self.flow.credentials
            service = build('oauth2', 'v2', credentials=credentials)
            
            print("[DEBUG] Attempting to fetch user info from Google")
            userinfo = service.userinfo().get().execute()
            
            # Log and validate the response
            print(f"[DEBUG] Received user info response: {userinfo}")
            
            if not userinfo:
                print("[ERROR] Empty response from userinfo endpoint")
                return None
                
            # Map 'id' to 'sub' if 'sub' is not present
            if 'id' in userinfo and 'sub' not in userinfo:
                userinfo['sub'] = userinfo['id']
                
            # Validate required fields
            required_fields = ['sub', 'email']
            missing_fields = [field for field in required_fields if field not in userinfo]
            if missing_fields:
                print(f"[ERROR] Missing required fields in user info: {missing_fields}")
                print(f"[DEBUG] Available fields: {list(userinfo.keys())}")
                return None
                
            return userinfo
        except Exception as e:
            print(f"[ERROR] Exception in get_user_info: {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def create_credentials(credentials_dict):
        """Create credentials object from dictionary."""
        try:
            return Credentials(
                token=credentials_dict['token'],
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict['token_uri'],
                client_id=credentials_dict['client_id'],
                client_secret=credentials_dict['client_secret'],
                scopes=credentials_dict['scopes']
            )
        except KeyError as e:
            raise Exception(f"Missing required credential field: {e}")