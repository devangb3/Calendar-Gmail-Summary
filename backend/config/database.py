from pymongo import MongoClient
from .settings import MONGO_URI, DATABASE_NAME

class Database:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if Database._instance is not None:
            raise Exception("Database class is a singleton!")
        
        self.client = None
        self.db = None
        self.users = None
        self.summaries = None
        self.initialize()
    
    def initialize(self):
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            self.users = self.db['users']
            self.summaries = self.db['summaries']
            
            # Create indexes
            self.users.create_index("user_id", unique=True)
            self.summaries.create_index([("user_id", 1), ("generated_at", -1)])
            
            # Test connection
            self.client.server_info()
            print("Successfully connected to MongoDB.")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            self.users = None
            self.summaries = None
    
    def is_connected(self):
        """Check if all database components are properly initialized and connected."""
        if None in (self.client, self.db, self.users, self.summaries):
            return False
            
        try:
            # Verify connection is still alive
            self.client.server_info()
            return True
        except Exception:
            return False
            
    def ensure_connected(self):
        """Ensure database connection is active, reinitialize if needed."""
        if not self.is_connected():
            self.initialize()
        return self.is_connected()