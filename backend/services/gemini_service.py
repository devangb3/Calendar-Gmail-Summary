import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from utils.logger import summary_logger, log_error

# Error messages
EMPTY_RESPONSE_ERROR = "Received empty response from Gemini API"
API_KEY_ERROR = "Gemini API key is not configured"
INIT_ERROR = "Failed to initialize Gemini model: {}"
RATE_LIMIT_ERROR = "API rate limit exceeded. Please try again later."
INVALID_KEY_ERROR = "Invalid API key configuration"
SUMMARY_ERROR = "Error generating summary: {}"
SMART_REPLY_ERROR = "Failed to generate smart replies: {}"

class GeminiServiceError(Exception):
    """Custom exception for Gemini service errors"""
    pass

class GeminiService:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise GeminiServiceError(API_KEY_ERROR)
            
        try:
            summary_logger.info("Initializing Gemini service")
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17')
            summary_logger.info("Gemini service initialized successfully")
        except Exception as e:
            log_error(summary_logger, e, "Failed to initialize Gemini service")
            raise GeminiServiceError(INIT_ERROR.format(str(e)))

    def generate_summary(self, calendar_events, emails):
        if not isinstance(calendar_events, list) or not isinstance(emails, list):
            raise ValueError("Calendar events and emails must be lists")

        try:
            summary_logger.info("Generating summary", 
                              extra={"num_events": len(calendar_events), "num_emails": len(emails)})

            # Format the events and emails into a prompt
            prompt = self._create_prompt(calendar_events, emails)
            
            # Generate the summary
            summary_logger.info("Sending request to Gemini API")
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                summary_logger.error("Received empty response from Gemini API")
                raise GeminiServiceError(EMPTY_RESPONSE_ERROR)

            summary_logger.info("Successfully generated summary")
            return self._clean_response(response.text)

        except Exception as e:
            log_error(summary_logger, e, "Failed to generate summary")
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                raise GeminiServiceError(RATE_LIMIT_ERROR)
            elif "invalid api key" in error_msg.lower():
                raise GeminiServiceError(INVALID_KEY_ERROR)
            else:
                raise GeminiServiceError(SUMMARY_ERROR.format(error_msg))

    def generate_smart_replies(self, thread):
        """Generate three smart reply suggestions for an email thread."""
        try:
            summary_logger.info("Generating smart replies")
            
            # Format the thread context
            messages = thread.get('messages', [])
            if not messages:
                raise ValueError("No messages in thread")
            
            # Create prompt for smart replies
            prompt = self._create_smart_reply_prompt(messages)
            
            # Generate the replies
            response = self.model.generate_content([
                {"text": prompt},
                {"text": "Generate exactly 3 concise, professional reply options, each starting with 'REPLY:' on a new line. Make them contextually appropriate, varying in tone from formal to casual but always professional."}
            ])
            
            if not response or not response.text:
                summary_logger.error("Received empty response from Gemini API")
                raise GeminiServiceError(EMPTY_RESPONSE_ERROR)
            
            # Parse the replies
            replies = []
            for line in response.text.split('\n'):
                if line.startswith('REPLY:'):
                    reply = line.replace('REPLY:', '').strip()
                    if reply:
                        replies.append(reply)
            
            # Ensure exactly 3 replies
            if len(replies) != 3:
                raise GeminiServiceError("Failed to generate the required number of replies")
                
            summary_logger.info("Successfully generated smart replies")
            return replies
            
        except Exception as e:
            log_error(summary_logger, e, "Failed to generate smart replies")
            raise GeminiServiceError(SMART_REPLY_ERROR.format(str(e)))

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
        try:
            summary_logger.debug("Creating prompt for summary generation")
            
            # Format calendar events
            events_text = self._format_events(calendar_events)
            emails_text = self._format_emails(emails)

            prompt = f"""Please provide a concise summary of today's calendar events and important emails. 
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
            summary_logger.debug("Successfully created prompt")
            return prompt

        except Exception as e:
            log_error(summary_logger, e, "Failed to create summary prompt")
            raise

    def _create_smart_reply_prompt(self, messages):
        thread_context = []
        separator = '-' * 40

        # Include up to 2 previous messages for context
        for msg in messages[-3:]:
            thread_context.append(
                f"From: {msg['from']}\n"
                f"Subject: {msg['subject']}\n"
                f"Content: {msg.get('body', msg['snippet'])}\n"
            )

        # Pre‑build the threaded text with actual newlines
        thread_text = "\n".join(thread_context)

        # Now use a clean triple‑quoted f‑string
        prompt = f"""Based on this email thread, generate appropriate reply suggestions:

        Thread Context:
        {separator}
        {thread_text}
        {separator}

        Consider:
        1. The tone and formality of previous messages
        2. Any specific questions or requests made
        3. Required next actions or decisions
        4. Professional email etiquette
        """
        """Create a prompt for smart reply generation"""
        
        return prompt

    def _format_events(self, events):
        if not events:
            return "No calendar events scheduled for today."
        
        formatted_events = []
        for event in events:
            if not isinstance(event, dict):
                continue
                
            attendees = ", ".join([a.get('email', '') for a in event.get('attendees', [])])
            event_lines = [
                f"- {event.get('summary', 'Untitled Event')}",
                f"  Time: {event.get('start', 'No start time')} - {event.get('end', 'No end time')}",
                f"  Location: {event.get('location', 'No location')}",
                f"  Attendees: {attendees if attendees else 'No attendees'}"
            ]
            formatted_events.append('\n'.join(event_lines))
            
        return '\n'.join(formatted_events) if formatted_events else "No valid calendar events found."

    def _format_emails(self, emails):
        if not emails:
            return "No new emails today."
        
        formatted_emails = []
        for email in emails:
            if not isinstance(email, dict):
                continue
                
            email_lines = [
                f"- Subject: {email.get('subject', 'No Subject')}",
                f"  From: {email.get('from', 'Unknown Sender')}",
                f"  Preview: {email.get('snippet', 'No preview available')}"
            ]
            formatted_emails.append('\n'.join(email_lines))
            
        return '\n'.join(formatted_emails) if formatted_emails else "No valid emails found."