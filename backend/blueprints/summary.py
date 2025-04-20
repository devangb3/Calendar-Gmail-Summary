from flask import Blueprint, jsonify, session
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService, GeminiServiceError
from utils.helpers import format_error_response
from utils.logger import summary_logger, log_error
from datetime import datetime, timedelta, timezone

summary_bp = Blueprint('summary', __name__)

@summary_bp.route('/summary')
def get_summary():
    try:
        summary_logger.info("Summary request initiated")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized summary request - no user_id in session")
            return format_error_response("Unauthorized", 401)

        # Get user and check credentials
        user = User.find_by_id(user_id)
        if not user:
            summary_logger.error(f"User {user_id} not found")
            return format_error_response("User not found", 401)
            
        credentials = user.credentials
        if not credentials:
            summary_logger.error(f"No valid credentials found for user {user_id}")
            return format_error_response("No valid credentials found", 401)

        # Check for cached summary
        cached_summary = Summary.get_recent_summary(user_id)
        if cached_summary and not _is_summary_stale(cached_summary):
            summary_logger.info(f"Returning cached summary for user {user_id}")
            return jsonify({
                "summary": cached_summary.summary_text,
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
            return format_error_response("Failed to initialize services", 500)

        # Fetch calendar events and emails
        try:
            summary_logger.info("Fetching calendar events and emails")
            events = calendar_service.get_events()
            emails = gmail_service.get_recent_emails()
            summary_logger.info(f"Fetched {len(events)} events and {len(emails)} emails")
        except Exception as e:
            log_error(summary_logger, e, "Failed to fetch events or emails")
            return format_error_response("Failed to fetch your data", 500)

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
            "cached": False,
            "generated_at": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        log_error(summary_logger, e, "Unexpected error in summary endpoint")
        return format_error_response(str(e), 500)

def _is_summary_stale(summary):
    """Check if a cached summary is too old to use"""
    if not summary or not summary.generated_at:
        return True
    
    # Both datetimes are now guaranteed to be timezone-aware in UTC
    age = datetime.now(timezone.utc) - summary.generated_at
    # Consider summary stale if it's more than 30 minutes old
    return age > timedelta(minutes=30)