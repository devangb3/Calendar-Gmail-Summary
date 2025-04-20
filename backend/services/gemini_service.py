import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

class GeminiServiceError(Exception):
    """Custom exception for Gemini service errors"""
    pass

class GeminiService:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise GeminiServiceError("Gemini API key is not configured")
            
        genai.configure(api_key=GEMINI_API_KEY)
        try:
            self.model = genai.GenerativeModel(GEMINI_MODEL)
        except Exception as e:
            raise GeminiServiceError(f"Failed to initialize Gemini model: {str(e)}")

    def generate_summary(self, calendar_events, emails):
        if not isinstance(calendar_events, list) or not isinstance(emails, list):
            raise ValueError("Calendar events and emails must be lists")

        prompt = self._create_prompt(calendar_events, emails)
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise GeminiServiceError("Received empty response from Gemini API")
                
            return self._clean_response(response.text)
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                raise GeminiServiceError("API rate limit exceeded. Please try again later.")
            elif "invalid api key" in error_msg.lower():
                raise GeminiServiceError("Invalid API key configuration")
            else:
                raise GeminiServiceError(f"Error generating summary: {error_msg}")

    def _clean_response(self, text):
        """Clean and validate the response text"""
        if not text:
            return None
            
        # Remove any markdown formatting if present
        text = text.replace('```', '').strip()
        
        # Ensure reasonable length
        if len(text) < 10:  # Too short to be meaningful
            return None
            
        return text

    def _create_prompt(self, calendar_events, emails):
        events_text = self._format_events(calendar_events)
        emails_text = self._format_emails(emails)

        return f"""Please provide a concise summary of today's calendar events and important emails. 
        Focus on key meetings, deadlines, and critical communications.

        Calendar Events:
        {events_text}

        Important Emails:
        {emails_text}

        Please format the summary in a clear, professional manner, highlighting:
        1. Key meetings and their times
        2. Important deadlines or action items
        3. Critical emails requiring attention
        4. Any follow-up tasks

        Keep the tone professional and the content focused on actionable items.
        
        If there are no events or emails, mention that explicitly."""

    def _format_events(self, events):
        if not events:
            return "No calendar events scheduled for today."
        
        formatted_events = []
        for event in events:
            if not isinstance(event, dict):
                continue
                
            attendees = ", ".join([a.get('email', '') for a in event.get('attendees', [])])
            formatted_events.append(
                f"- {event.get('summary', 'Untitled Event')}\n"
                f"  Time: {event.get('start', 'No start time')} - {event.get('end', 'No end time')}\n"
                f"  Location: {event.get('location', 'No location')}\n"
                f"  Attendees: {attendees if attendees else 'No attendees'}\n"
            )
        return "\n".join(formatted_events) if formatted_events else "No valid calendar events found."

    def _format_emails(self, emails):
        if not emails:
            return "No new emails today."
        
        formatted_emails = []
        for email in emails:
            if not isinstance(email, dict):
                continue
                
            formatted_emails.append(
                f"- Subject: {email.get('subject', 'No Subject')}\n"
                f"  From: {email.get('from', 'Unknown Sender')}\n"
                f"  Preview: {email.get('snippet', 'No preview available')}\n"
            )
        return "\n".join(formatted_emails) if formatted_emails else "No valid emails found."