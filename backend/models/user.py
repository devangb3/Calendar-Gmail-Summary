from datetime import datetime
from config.database import Database
from config.settings import SCOPES

class User:
    def __init__(self, user_id, email, name):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.db = Database.get_instance()

    @staticmethod
    def find_by_id(user_id):
        db = Database.get_instance()
        if db is None or not db.is_connected():
            return None
        
        user_data = db.users.find_one({'user_id': user_id})
        if user_data:
            return User(user_data['user_id'], user_data['email'], user_data['name'])
        return None

    def save_credentials(self, credentials_dict):
        """Save or update user credentials, handling scope changes."""
        if self.db is None or not self.db.is_connected():
            raise Exception("Database not connected")
        
        # Verify all required scopes are present
        if 'scopes' in credentials_dict:
            required_scopes = set(SCOPES)
            granted_scopes = set(credentials_dict['scopes'])
            if not required_scopes.issubset(granted_scopes):
                raise Exception("Missing required scopes")

        update_data = {
            'email': self.email,
            'name': self.name,
            'credentials': credentials_dict,
            'updated_at': datetime.utcnow(),
            'last_token_refresh': datetime.utcnow()
        }

        # If this is a new user, include creation timestamp
        result = self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$set': update_data,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None

    def get_credentials(self):
        """Get user credentials, verifying scope compatibility."""
        if self.db is None or not self.db.is_connected():
            return None
        
        user_data = self.db.users.find_one({'user_id': self.user_id})
        if not user_data or 'credentials' not in user_data:
            return None

        credentials = user_data['credentials']
        
        # Verify scope compatibility
        if 'scopes' in credentials:
            required_scopes = set(SCOPES)
            stored_scopes = set(credentials['scopes'])
            if not required_scopes.issubset(stored_scopes):
                # If scopes are incompatible, remove credentials to force re-auth
                self.remove_credentials()
                return None
                
        return credentials

    def update_credentials(self, new_credentials_dict):
        """Update user credentials after a refresh."""
        if self.db is None or not self.db.is_connected():
            raise Exception("Database not connected")
        
        return self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$set': {
                    'credentials': new_credentials_dict,
                    'updated_at': datetime.utcnow(),
                    'last_token_refresh': datetime.utcnow()
                }
            }
        )

    def remove_credentials(self):
        """Remove user credentials."""
        if self.db is None or not self.db.is_connected():
            raise Exception("Database not connected")
        
        return self.db.users.update_one(
            {'user_id': self.user_id},
            {
                '$unset': {'credentials': ""},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )