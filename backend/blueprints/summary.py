from flask import Blueprint, jsonify, session, request
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService, GeminiServiceError
from services.scheduler_service import SchedulerService
from utils.helpers import format_error_response
from utils.logger import summary_logger, log_error
from datetime import datetime, timedelta, timezone

# Error messages
INIT_SERVICES_ERROR = "Failed to initialize services"
FETCH_DATA_ERROR = "Failed to fetch your data"
FETCH_THREAD_ERROR = "Failed to fetch email thread"
UNAUTHORIZED_ERROR = "Unauthorized"
USER_NOT_FOUND_ERROR = "User not found"
NO_CREDENTIALS_ERROR = "No valid credentials found"
MISSING_FIELDS_ERROR = "Missing required fields"
SEND_REPLY_ERROR = "Failed to send reply"
DB_UNAVAILABLE_ERROR = "Database service unavailable"

summary_bp = Blueprint('summary', __name__)
scheduler_service = SchedulerService.get_instance()

@summary_bp.route('/summary')
def get_summary():
    try:
        summary_logger.info("Summary request initiated")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized summary request - no user_id in session")
            return format_error_response(UNAUTHORIZED_ERROR, 401)

        # Get user and check credentials
        user = User.find_by_id(user_id)
        if not user:
            summary_logger.error(f"User {user_id} not found")
            return format_error_response(USER_NOT_FOUND_ERROR, 401)
            
        credentials = user.credentials
        if not credentials:
            summary_logger.error(f"No valid credentials found for user {user_id}")
            return format_error_response(NO_CREDENTIALS_ERROR, 401)

        # Check for query parameter indicating refresh request
        force_refresh = request.args.get('refresh', '').lower() == 'true'
        
        # Check for cached summary if not forcing refresh
        if not force_refresh:
            cached_summary = Summary.get_recent_summary(user_id)
            if cached_summary and not _is_summary_stale(cached_summary):
                summary_logger.info(f"Returning cached summary for user {user_id}")
                calendar_service = CalendarService(credentials)
                gmail_service = GmailService(credentials)
                try:
                    events = calendar_service.get_events()
                    emails = gmail_service.get_recent_emails()
                    return jsonify({
                        "summary": cached_summary.summary_text,
                        "emails": emails,
                        "events": events,
                        "cached": True,
                        "generated_at": cached_summary.generated_at.isoformat()
                    })
                except Exception as e:
                    log_error(summary_logger, e, "Failed to fetch data for cached summary")
                    return jsonify({
                        "summary": cached_summary.summary_text,
                        "cached": True,
                        "generated_at": cached_summary.generated_at.isoformat()
                    })

        # Force refresh or no valid cache - use scheduler to refresh digest
        try:
            summary_logger.info(f"Refreshing digest for user {user_id}")
            result = scheduler_service.refresh_user_digest(user_id)
            if not result:
                return format_error_response("Failed to refresh digest", 500)
            return jsonify(result)
        except Exception as e:
            log_error(summary_logger, e, "Failed to refresh digest")
            return format_error_response(str(e), 500)

    except Exception as e:
        log_error(summary_logger, e, "Unexpected error in summary endpoint")
        return format_error_response(str(e), 500)

@summary_bp.route('/smart-replies/<thread_id>')
def get_smart_replies(thread_id):
    try:
        summary_logger.info(f"Smart replies request initiated for thread: {thread_id}")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized smart replies request")
            return format_error_response(UNAUTHORIZED_ERROR, 401)

        # Get user and check credentials
        user = User.find_by_id(user_id)
        if not user:
            summary_logger.error(f"User {user_id} not found")
            return format_error_response(USER_NOT_FOUND_ERROR, 401)
            
        credentials = user.credentials
        if not credentials:
            summary_logger.error(f"No valid credentials found for user {user_id}")
            return format_error_response(NO_CREDENTIALS_ERROR, 401)

        # Initialize services
        try:
            gmail_service = GmailService(credentials)
            gemini_service = GeminiService()
        except Exception as e:
            log_error(summary_logger, e, "Failed to initialize services")
            return format_error_response(INIT_SERVICES_ERROR, 500)

        # Get thread details
        try:
            thread = gmail_service.get_thread(thread_id)
        except Exception as e:
            log_error(summary_logger, e, "Failed to fetch thread")
            return format_error_response(FETCH_THREAD_ERROR, 500)

        # Generate smart replies
        try:
            replies = gemini_service.generate_smart_replies(thread)
            return jsonify({
                "replies": replies,
                "thread": thread
            })
        except Exception as e:
            log_error(summary_logger, e, "Failed to generate smart replies")
            return format_error_response(str(e), 500)

    except Exception as e:
        log_error(summary_logger, e, "Unexpected error in smart replies endpoint")
        return format_error_response(str(e), 500)

@summary_bp.route('/send-reply', methods=['POST'])
def send_reply():
    try:
        summary_logger.info("Send reply request initiated")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized send reply request")
            return format_error_response(UNAUTHORIZED_ERROR, 401)

        data = request.get_json()
        if not data or 'threadId' not in data or 'reply' not in data or 'to' not in data:
            return format_error_response(MISSING_FIELDS_ERROR, 400)

        # Get user and check credentials
        user = User.find_by_id(user_id)
        if not user or not user.credentials:
            return format_error_response(UNAUTHORIZED_ERROR, 401)

        # Initialize Gmail service
        try:
            gmail_service = GmailService(user.credentials)
        except Exception as e:
            log_error(summary_logger, e, "Failed to initialize Gmail service")
            return format_error_response(INIT_SERVICES_ERROR, 500)

        # Send the reply
        try:
            sent_message = gmail_service.send_email(
                to=data['to'],
                subject=data.get('subject', 'Re: '),  # Use original subject if not provided
                body=data['reply'],
                thread_id=data['threadId']
            )
            return jsonify({
                "success": True,
                "messageId": sent_message['id']
            })
        except Exception as e:
            log_error(summary_logger, e, "Failed to send reply")
            return format_error_response(SEND_REPLY_ERROR, 500)

    except Exception as e:
        log_error(summary_logger, e, "Unexpected error in send reply endpoint")
        return format_error_response(str(e), 500)

def _is_summary_stale(summary):
    """Check if a cached summary is too old to use"""
    if not summary or not summary.generated_at:
        return True
    
    # Both datetimes are now guaranteed to be timezone-aware in UTC
    age = datetime.now(timezone.utc) - summary.generated_at
    # Consider summary stale if it's more than 30 minutes old
    return age > timedelta(minutes=30)