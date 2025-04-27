import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils.logger import auth_logger, log_error
from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    CLIENT_SECRETS_FILE,
    SCOPES
)

class AuthServiceError(Exception):
    """Base exception for authentication service errors."""
    pass

class ScopeMismatchError(AuthServiceError):
    """Exception raised when OAuth scopes don't match requirements."""
    pass

class CredentialsError(AuthServiceError):
    """Exception raised when there are issues with credentials."""
    pass

class AuthService:
    def __init__(self):
        self.flow = None
        self.state = None

    def _create_flow(self):
        """Create a new OAuth flow instance."""
        try:
            return Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=GOOGLE_REDIRECT_URI
            )
        except Exception as e:
            log_error(auth_logger, e, "Failed to create OAuth flow")
            raise

    def get_authorization_url(self):
        """Generate the authorization URL for Google OAuth."""
        try:
            self.flow = self._create_flow()
            authorization_url, state = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='false',  # Don't include previously granted scopes
                prompt='consent',  # Always show consent screen
                state='calendar_summary_auth'
            )
            self.state = state
            auth_logger.info(f"Generated authorization URL successfully: {authorization_url}")
            return authorization_url
        except Exception as e:
            log_error(auth_logger, e, "Failed to generate authorization URL")
            raise

    def get_token(self, authorization_response, base_url):
        """Exchange authorization code for tokens."""
        try:
            # Create new flow if none exists (e.g. after server restart)
            if not self.flow:
                auth_logger.info("No existing flow found, creating new one")
                self.flow = self._create_flow()

            auth_logger.debug("Fetching token with authorization response")
            self.flow.fetch_token(
                authorization_response=authorization_response,
                authorization_base_url=base_url
            )
            
            granted_scopes = set(self.flow.credentials.scopes)
            required_scopes = set(SCOPES)
            
            # Check for exact scope match instead of subset
            if required_scopes != granted_scopes:
                missing_scopes = required_scopes - granted_scopes
                extra_scopes = granted_scopes - required_scopes
                error_msg = []
                if missing_scopes:
                    error_msg.append(f"Missing required scopes: {', '.join(missing_scopes)}")
                if extra_scopes:
                    error_msg.append(f"Extra scopes granted: {', '.join(extra_scopes)}")
                raise ScopeMismatchError(". ".join(error_msg))
            
            auth_logger.info("Successfully obtained access token with correct scopes")
            return {
                'token': self.flow.credentials.token,
                'refresh_token': self.flow.credentials.refresh_token,
                'token_uri': self.flow.credentials.token_uri,
                'client_id': self.flow.credentials.client_id,
                'client_secret': self.flow.credentials.client_secret,
                'scopes': list(granted_scopes)
            }
        except Exception as e:
            log_error(auth_logger, e, "Failed to fetch token")
            raise

    def get_user_info(self):
        """Get user information from Google."""
        try:
            if not self.flow or not self.flow.credentials:
                auth_logger.error("No valid OAuth flow or credentials available")
                return None
                
            auth_logger.debug("Attempting to fetch user info from Google")
            service = build('oauth2', 'v2', credentials=self.flow.credentials)
            userinfo = service.userinfo().get().execute()
            
            if not userinfo:
                auth_logger.error("Empty response from userinfo endpoint")
                return None
                
            # Map 'id' to 'sub' if 'sub' is not present
            if 'id' in userinfo and 'sub' not in userinfo:
                userinfo['sub'] = userinfo['id']
                
            required_fields = ['sub', 'email']
            missing_fields = [field for field in required_fields if field not in userinfo]
            if missing_fields:
                auth_logger.error(f"Missing required fields: {missing_fields}")
                return None
                
            auth_logger.info("Successfully retrieved user info")
            return userinfo
        except Exception as e:
            log_error(auth_logger, e, "Failed to get user info")
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
            raise CredentialsError(f"Missing required credential field: {e}")