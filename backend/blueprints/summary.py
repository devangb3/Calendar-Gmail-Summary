from flask import Blueprint, jsonify, session
from models.user import User
from models.summary import Summary
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from services.gemini_service import GeminiService
from utils.helpers import handle_api_error
from config.database import Database

summary_bp = Blueprint('summary', __name__)

@summary_bp.route('/summary')
def get_summary():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        # Ensure database is connected
        db = Database.get_instance()
        if db is None or not db.ensure_connected():
            return jsonify({"error": "Database service unavailable"}), 503

        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        credentials = user.get_credentials()
        if not credentials:
            return jsonify({"error": "No credentials found"}), 401

        # Check for recent cached summary
        cached_summary = Summary.get_recent_summary(user_id)
        if cached_summary is not None:
            return jsonify({"summary": cached_summary.summary_text})

        # Get calendar events and emails
        calendar_service = CalendarService(credentials)
        gmail_service = GmailService(credentials)
        gemini_service = GeminiService()

        try:
            events = calendar_service.get_today_events()
            emails = gmail_service.get_today_emails()
        except Exception as e:
            return jsonify(handle_api_error(e)), 500

        # Generate summary using Gemini
        try:
            summary_text = gemini_service.generate_summary(events, emails)
            if not summary_text:
                return jsonify({"error": "Failed to generate summary"}), 500
        except Exception as e:
            return jsonify({"error": f"Error generating summary: {str(e)}"}), 500

        # Save the new summary
        try:
            summary = Summary(user_id, summary_text)
            summary.save()
        except Exception as e:
            # If saving fails, still return the generated summary
            print(f"Warning: Failed to cache summary: {e}")
            return jsonify({"summary": summary_text, "cached": False})

        return jsonify({
            "summary": summary_text,
            "cached": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500