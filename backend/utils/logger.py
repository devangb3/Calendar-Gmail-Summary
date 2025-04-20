import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure different loggers for different purposes
def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as needed"""
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, log_file),
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Add console handler for non-production environments
    if os.environ.get('FLASK_ENV') != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Create specific loggers
auth_logger = setup_logger('auth', 'auth.log')
api_logger = setup_logger('api', 'api.log')
db_logger = setup_logger('db', 'database.log')
summary_logger = setup_logger('summary', 'summary.log')

def log_error(logger, error, context=None):
    """Utility function to log errors with context"""
    error_message = f"Error: {str(error)}"
    if context:
        error_message = f"{context} - {error_message}"
    logger.error(error_message)
    if hasattr(error, '__traceback__'):
        logger.exception(error)