import os
from flask import session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

from utils.logger import auth_logger, log_error
from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    CLIENT_SECRETS_FILE,
    SCOPES,
    FRONTEND_URL
)
from models.user import User

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
        self._credentials = None
        auth_logger.info("AuthService initialized")

    def get_authorization_url(self):
        """Generate authorization URL for OAuth flow"""
        try:
            auth_logger.info("Generating authorization URL")
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=GOOGLE_REDIRECT_URI
            )
            # Store flow state in session
            auth_logger.info("Created flow", flow)
            session['flow_state'] = {
                'client_id': flow.client_config['client_id'],
                'client_secret': flow.client_config['client_secret'],
                'redirect_uri': flow.redirect_uri,
                'scopes': SCOPES
            }
            
            auth_logger.info(f"Flow redirect URI: {flow.redirect_uri}")
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            auth_logger.info("Authorization URL generated successfully")
            return authorization_url
        except Exception as e:
            auth_logger.error(f"Error generating authorization URL: {str(e)}")
            raise

    def get_token(self, authorization_response, base_url):
        """Exchange authorization code for tokens"""
        try:
            auth_logger.info("Exchanging authorization code for tokens")
            auth_logger.info(f"Authorization response URL: {authorization_response}")
            auth_logger.info(f"Base URL: {base_url}")
            auth_logger.info(f"Session before token exchange: {dict(session)}")
            # Retrieve flow state from session
            flow_state = session.get('flow_state')
            if not flow_state:
                auth_logger.error("Flow state not found in session")
                raise ValueError("Authorization flow not initialized")

            # Recreate flow from session state
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=flow_state['scopes'],
                redirect_uri=flow_state['redirect_uri']
            )

            # Fetch the token
            flow.fetch_token(authorization_response=authorization_response)
            self._credentials = flow.credentials
            
            # Clean up session
            if 'flow_state' in session:
                del session['flow_state']
            
            auth_logger.info("Token exchange successful")
            auth_logger.info(f"Credentials valid: {self._credentials.valid}")
            auth_logger.info(f"Credentials expired: {self._credentials.expired}")
            
            # Convert credentials to dict for storage
            creds_dict = self._credentials_to_dict(self._credentials)
            auth_logger.info(f"Credentials type and presence of token: {{'type': {type(creds_dict)}, 'has_token': bool(creds_dict.get('token'))}}")
            
            return creds_dict
        except Exception as e:
            auth_logger.error(f"Token exchange error: {str(e)}")
            raise

    def get_user_info(self):
        """Get user info from Google"""
        try:
            auth_logger.info("Fetching user info")
            if not self._credentials or not self._credentials.valid:
                auth_logger.error("Invalid credentials when fetching user info")
                return None

            service = build('oauth2', 'v2', credentials=self._credentials)
            user_info = service.userinfo().get().execute()
            auth_logger.info(f"Raw user info response: {user_info}")
            
            # Ensure we have a user ID (sub or id)
            if 'sub' not in user_info and 'id' in user_info:
                user_info['sub'] = user_info['id']
                auth_logger.info("Using 'id' as 'sub' for user identification")
            
            if 'sub' not in user_info:
                auth_logger.error("No user ID found in response")
                raise ValueError("No user ID (sub) found in Google response")
                
            auth_logger.info(f"User info processed successfully for email: {user_info.get('email')}")
            return user_info
        except Exception as e:
            auth_logger.error(f"Error fetching user info: {str(e)}")
            raise

    def _credentials_to_dict(self, credentials):
        """Convert Google credentials to dict for storage"""
        try:
            auth_logger.info("Converting credentials to dict")
            return {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        except Exception as e:
            auth_logger.error(f"Error converting credentials to dict: {str(e)}")
            raise