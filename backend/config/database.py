from pymongo import MongoClient
from .settings import MONGO_URI, DATABASE_NAME
from utils.logger import db_logger, log_error

class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass

class DatabaseInitializationError(DatabaseError):
    """Exception raised when database initialization fails."""
    pass

# Error message constants
DB_ERROR_MESSAGES = {
    'connection': "Database not available",
    'singleton': "Database class is a singleton!"
}

class Database:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if Database._instance is not None:
            raise DatabaseInitializationError(DB_ERROR_MESSAGES['singleton'])
        
        self.client = None
        self.db = None
        self.users = None
        self.summaries = None
        self.initialize()
    
    def initialize(self):
        try:
            db_logger.info("Initializing database connection")
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            self.users = self.db['users']
            self.summaries = self.db['summaries']
            
            # Create indexes
            db_logger.info("Creating database indexes")
            self.users.create_index("user_id", unique=True)
            self.summaries.create_index([("user_id", 1), ("generated_at", -1)])
            
            # Test connection
            self.client.server_info()
            db_logger.info("Successfully connected to MongoDB")
        except Exception as e:
            log_error(db_logger, e, "Failed to initialize database connection")
            self.client = None
            self.db = None
            self.users = None
            self.summaries = None
            raise DatabaseConnectionError("Failed to initialize database connection") from e
    
    def is_connected(self):
        """Check if all database components are properly initialized and connected."""
        if None in (self.client, self.db, self.users, self.summaries):
            db_logger.warning("Database components not fully initialized")
            return False
            
        try:
            # Verify connection is still alive
            self.client.server_info()
            return True
        except Exception as e:
            log_error(db_logger, e, "Database connection check failed")
            return False
            
    def ensure_connected(self):
        """Ensure database connection is active, reinitialize if needed."""
        if not self.is_connected():
            db_logger.info("Attempting to reinitialize database connection")
            self.initialize()
        return self.is_connected()