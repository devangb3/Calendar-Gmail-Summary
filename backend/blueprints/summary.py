from flask import Blueprint, jsonify, session, request
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService, GeminiServiceError
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

        # Check for cached summary
        cached_summary = Summary.get_recent_summary(user_id)
        if cached_summary and not _is_summary_stale(cached_summary):
            summary_logger.info(f"Returning cached summary for user {user_id}")
            # Get fresh emails and events even when using cached summary
            try:
                calendar_service = CalendarService(credentials)
                gmail_service = GmailService(credentials)
                events = calendar_service.get_events()
                emails = gmail_service.get_recent_emails()
            except Exception as e:
                log_error(summary_logger, e, "Failed to fetch data for cached summary")
                # Continue with just the summary if data fetch fails
                return jsonify({
                    "summary": cached_summary.summary_text,
                    "cached": True,
                    "generated_at": cached_summary.generated_at.isoformat()
                })

            return jsonify({
                "summary": cached_summary.summary_text,
                "emails": emails,
                "events": events,
                "cached": True,
                "generated_at": cached_summary.generated_at.isoformat()
            })

        # Initialize services
        try:
            summary_logger.info("Initializing services for fresh summary generation")
            calendar_service = CalendarService(credentials)
            gmail_service = GmailService(credentials)
            gemini_service = GeminiService()
        except Exception as e:
            log_error(summary_logger, e, "Failed to initialize services")
            return format_error_response(INIT_SERVICES_ERROR, 500)

        # Fetch calendar events and emails
        try:
            summary_logger.info("Fetching calendar events and emails")
            events = calendar_service.get_events()
            emails = gmail_service.get_recent_emails()
            summary_logger.info(f"Fetched {len(events)} events and {len(emails)} emails")
        except Exception as e:
            log_error(summary_logger, e, "Failed to fetch events or emails")
            return format_error_response(FETCH_DATA_ERROR, 500)

        # Generate summary
        try:
            summary_logger.info("Generating new summary")
            summary_text = gemini_service.generate_summary(events, emails)
            if not summary_text:
                summary_logger.error("Received empty summary from Gemini service")
                return format_error_response("Failed to generate summary", 500)
        except GeminiServiceError as e:
            log_error(summary_logger, e, "Gemini service error")
            return format_error_response(str(e), 500)
        except Exception as e:
            log_error(summary_logger, e, "Unexpected error during summary generation")
            return format_error_response("Failed to generate summary", 500)

        # Save new summary
        try:
            summary_logger.info(f"Saving new summary for user {user_id}")
            summary = Summary(user_id, summary_text)
            summary.save()
        except Exception as e:
            log_error(summary_logger, e, "Failed to save summary")
            # Continue anyway since we have the summary text
            
        summary_logger.info("Summary generation completed successfully")
        return jsonify({
            "summary": summary_text,
            "emails": emails,  # Include emails in response
            "events": events,  # Include events in response
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat()
        })

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