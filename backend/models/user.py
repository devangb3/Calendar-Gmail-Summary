from datetime import datetime, timezone
from config.database import Database, DatabaseError, DatabaseConnectionError, DB_ERROR_MESSAGES
from config.settings import SCOPES
from utils.logger import db_logger as logger

class UserError(Exception):
    """Base exception for user-related errors."""
    pass

class InvalidScopesError(UserError):
    """Exception raised when OAuth scopes are invalid or missing."""
    pass

class User:
    def __init__(self, user_id, email, name):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.db = Database.get_instance()
        self._credentials = None

    @property
    def credentials(self):
        """Get user credentials, loading from DB if needed."""
        if self._credentials is None:
            self._credentials = self.get_credentials()
        return self._credentials

    @staticmethod
    def find_by_id(user_id):
        db = Database.get_instance()
        if db is None or not db.is_connected():
            raise DatabaseConnectionError(DB_ERROR_MESSAGES['connection'])
        
        user_data = db.users.find_one({'user_id': user_id})
        if user_data:
            user = User(user_data['user_id'], user_data['email'], user_data['name'])
            if 'credentials' in user_data:
                user._credentials = user_data['credentials']
            return user
        return None

    def save_credentials(self, credentials_dict):
        """Save or update user credentials, handling scope changes."""
        if self.db is None or not self.db.is_connected():
            raise DatabaseConnectionError(DB_ERROR_MESSAGES['connection'])
        
        # Verify all required scopes are present
        if 'scopes' in credentials_dict:
            required_scopes = set(SCOPES)
            granted_scopes = set(credentials_dict['scopes'])
            
            # Check if there's a scope mismatch
            if required_scopes != granted_scopes:
                logger.warning(f"Scope mismatch for user {self.user_id}. Required: {required_scopes}, Granted: {granted_scopes}")
                # Remove credentials to force re-auth with correct scopes
                self.remove_credentials()
                raise InvalidScopesError(f"Scope has changed from \"{' '.join(granted_scopes)}\" to \"{' '.join(required_scopes)}\".")

        update_data = {
            'email': self.email,
            'name': self.name,
            'credentials': credentials_dict,
            'updated_at': datetime.now(timezone.utc),
            'last_token_refresh': datetime.now(timezone.utc)
        }

        # If this is a new user, include creation timestamp
        result = self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$set': update_data,
                '$setOnInsert': {'created_at': datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None

    def get_credentials(self):
        """Get user credentials, verifying scope compatibility."""
        if self.db is None or not self.db.is_connected():
            raise DatabaseConnectionError(DB_ERROR_MESSAGES['connection'])
        
        user_data = self.db.users.find_one({'user_id': self.user_id})
        if not user_data or 'credentials' not in user_data:
            return None

        credentials = user_data['credentials']
        
        # Always verify scope compatibility
        if 'scopes' in credentials:
            required_scopes = set(SCOPES)
            stored_scopes = set(credentials['scopes'])
            
            # Check for exact scope match
            if required_scopes != stored_scopes:
                logger.warning(f"Scope mismatch for user {self.user_id}. Required: {required_scopes}, Stored: {stored_scopes}")
                # Remove credentials to force re-auth with correct scopes
                self.remove_credentials()
                return None
                
        return credentials

    def update_credentials(self, new_credentials_dict):
        """Update user credentials after a refresh."""
        if self.db is None or not self.db.is_connected():
            raise DatabaseConnectionError(DB_ERROR_MESSAGES['connection'])
        
        return self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$set': {
                    'credentials': new_credentials_dict,
                    'updated_at': datetime.now(timezone.utc),
                    'last_token_refresh': datetime.now(timezone.utc)
                }
            }
        )

    def remove_credentials(self):
        """Remove user credentials."""
        if self.db is None or not self.db.is_connected():
            raise DatabaseConnectionError(DB_ERROR_MESSAGES['connection'])
        
        return self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$unset': {'credentials': ""},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )