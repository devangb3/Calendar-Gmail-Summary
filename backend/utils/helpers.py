from datetime import datetime
from typing import Dict, Any, Optional, Union
import re

def format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p, %B %d, %Y")
    except Exception:
        return timestamp

def sanitize_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def validate_credentials(credentials: Dict[str, Any]) -> bool:
    """Validate that all required credential fields are present."""
    required_fields = ['token', 'token_uri', 'client_id', 'client_secret', 'scopes']
    return all(field in credentials for field in required_fields)

def handle_api_error(error: Exception) -> Dict[str, str]:
    """Format API errors for consistent response."""
    error_type = type(error).__name__
    error_message = str(error)
    
    error_mapping = {
        'invalid_grant': {
            "error": "Authentication Error",
            "message": "Your session has expired. Please log in again."
        },
        'quota': {
            "error": "Rate Limit Error",
            "message": "API quota exceeded. Please try again later."
        },
        'invalid_token': {
            "error": "Authentication Error",
            "message": "Invalid or expired token. Please log in again."
        },
        'access_denied': {
            "error": "Authorization Error",
            "message": "Access denied. Please check your permissions and try again."
        },
        'service_unavailable': {
            "error": "Service Error",
            "message": "Service is temporarily unavailable. Please try again later."
        }
    }
    
    # Check for known error patterns
    for key, response in error_mapping.items():
        if key in error_message.lower():
            return response
    
    # Handle database-specific errors
    if 'mongodb' in error_message.lower():
        return {
            "error": "Database Error",
            "message": "Database operation failed. Please try again later."
        }
    
    # Default error response
    return {
        "error": error_type,
        "message": error_message
    }

def is_valid_email(email: str) -> bool:
    """Validate email format."""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError, AttributeError):
        return default

def format_error_response(
    error: Union[str, Exception],
    status_code: int = 500,
    additional_info: Optional[Dict[str, Any]] = None
) -> tuple:
    """Format error response with consistent structure."""
    response = {
        "error": str(error),
        "status": status_code
    }
    
    if additional_info:
        response.update(additional_info)
        
    return response, status_code