from flask import Blueprint, jsonify, session, request, send_file
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService, GeminiServiceError
from services.scheduler_service import SchedulerService
from services.tts_service import TTSService
from utils.helpers import format_error_response
from utils.logger import summary_logger, log_error
from datetime import datetime, timedelta, timezone
import os

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
                return jsonify({
                    "summary": cached_summary.summary_text,
                    "cached": True,
                    "generated_at": cached_summary.generated_at.isoformat()
                })

        # Force refresh or no valid cache - use scheduler to refresh digest
        try:
            summary_logger.info(f"Refreshing digest for user {user_id}")
            calendar_service = CalendarService(credentials)
            gmail_service = GmailService(credentials)

            events = calendar_service.get_events(
                time_min=datetime.now(timezone.utc).isoformat(),
                time_max=(datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
            )
            raw_emails = gmail_service.get_recent_emails(max_results=10)  # Get up to 20 emails for summary
            
            # Format emails to ensure threadId and other required fields are included
            formatted_emails = []
            for email in raw_emails:
                if email and email.get('threadId'):  # Only include emails with valid threadId
                    formatted_emails.append({
                        'subject': email.get('subject', 'No Subject'),
                        'from': email.get('from', 'Unknown Sender'),
                        'from_email': email.get('from_email'),  # Include from_email field
                        'threadId': email['threadId'],
                        'snippet': email.get('snippet', ''),
                        'date': email.get('date', ''),
                        'id': email.get('id', '')
                    })
            
            # Generate structured summary through Gemini
            gemini_service = GeminiService()
            summary_text = gemini_service.generate_summary(events, formatted_emails)
            
            # Save the summary
            summary = Summary(user_id, summary_text)
            summary.save()
            
            return jsonify({
                "summary": summary_text,
                "cached": False,
                "generated_at": datetime.now(timezone.utc).isoformat()
            })
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
        
        # Validate thread_id
        if not thread_id or thread_id == 'null' or thread_id == 'undefined':
            summary_logger.error("Invalid thread_id received")
            return format_error_response("Invalid thread ID", 400)
            
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

@summary_bp.route('/audio-summary')
def get_audio_summary():
    """Generate and return an audio version of the current summary"""
    try:
        summary_logger.info("Audio summary request initiated")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized audio summary request")
            return format_error_response(UNAUTHORIZED_ERROR, 401)

        # Get recent summary from database
        cached_summary = Summary.get_recent_summary(user_id)
        if not cached_summary:
            return format_error_response("No recent summary available", 404)
            
        # Generate audio from summary
        tts_service = TTSService()
        audio_file = tts_service.generate_audio_summary(cached_summary.summary_text)
        
        try:
            response = send_file(
                audio_file,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name='summary.mp3'
            )
            # Add CORS headers specifically for audio streaming
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            return response
        finally:
            # Clean up the temporary file after sending
            if os.path.exists(audio_file):
                os.unlink(audio_file)
                
    except Exception as e:
        log_error(summary_logger, e, "Failed to generate audio summary")
        return format_error_response(str(e), 500)

@summary_bp.route('/pending-invites')
def get_pending_invites():
    """Get list of pending calendar invitations"""
    try:
        summary_logger.info("Pending invites request initiated")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized pending invites request")
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

        # Get pending invites using calendar service
        calendar_service = CalendarService(credentials)
        pending_invites = calendar_service.get_pending_invites()
        
        return jsonify({
            "pending_invites": pending_invites
        })

    except Exception as e:
        log_error(summary_logger, e, "Failed to get pending invites")
        return format_error_response(str(e), 500)

@summary_bp.route('/accept-invite/<event_id>', methods=['POST'])
def accept_invite(event_id):
    """Accept a calendar invitation"""
    try:
        summary_logger.info(f"Accept invite request initiated for event: {event_id}")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized accept invite request")
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

        # Accept invite using calendar service
        calendar_service = CalendarService(credentials)
        success = calendar_service.accept_calendar_invite(event_id)
        
        return jsonify({
            "success": success,
            "message": "Calendar invite accepted successfully" if success else "Failed to accept invite"
        })

    except Exception as e:
        log_error(summary_logger, e, "Failed to accept calendar invite")
        return format_error_response(str(e), 500)

@summary_bp.route('/decline-invite/<event_id>', methods=['POST'])
def decline_invite(event_id):
    """Decline a calendar invitation"""
    try:
        summary_logger.info(f"Decline invite request initiated for event: {event_id}")
        user_id = session.get('user_id')
        if not user_id:
            summary_logger.warning("Unauthorized decline invite request")
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

        # Decline invite using calendar service
        calendar_service = CalendarService(credentials)
        success = calendar_service.decline_calendar_invite(event_id)
        
        return jsonify({
            "success": success,
            "message": "Calendar invite declined successfully" if success else "Failed to decline invite"
        })

    except Exception as e:
        log_error(summary_logger, e, "Failed to decline calendar invite")
        return format_error_response(str(e), 500)

def _is_summary_stale(summary):
    """Check if a cached summary is too old to use"""
    if not summary or not summary.generated_at:
        return True
    
    # Both datetimes are now guaranteed to be timezone-aware in UTC
    age = datetime.now(timezone.utc) - summary.generated_at
    # Consider summary stale if it's more than 30 minutes old
    return age > timedelta(minutes=30)