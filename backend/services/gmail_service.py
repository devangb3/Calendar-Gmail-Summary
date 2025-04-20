from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from utils.logger import api_logger, log_error
import base64
import email

class GmailService:
    def __init__(self, credentials_dict):
        try:
            api_logger.info("Initializing Gmail service")
            credentials = Credentials(
                token=credentials_dict['token'],
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict['token_uri'],
                client_id=credentials_dict['client_id'],
                client_secret=credentials_dict['client_secret'],
                scopes=credentials_dict['scopes']
            )
            self.service = build('gmail', 'v1', credentials=credentials)
            api_logger.info("Gmail service initialized successfully")
        except Exception as e:
            log_error(api_logger, e, "Failed to initialize Gmail service")
            raise

    def get_recent_emails(self, max_results=20):
        try:
            api_logger.info(f"Fetching recent emails, max_results={max_results}")
            time_threshold = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y/%m/%d')
            
            query = f'after:{time_threshold}'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            api_logger.info(f"Found {len(messages)} recent emails")

            emails = []
            for message in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    emails.append(self._parse_message(msg))
                except Exception as e:
                    log_error(api_logger, e, f"Failed to fetch email details for ID: {message['id']}")
                    continue

            api_logger.info(f"Successfully processed {len(emails)} emails")
            return emails

        except Exception as e:
            log_error(api_logger, e, "Failed to fetch recent emails")
            raise

    def _extract_email(self, address_string):
        """Extract email address from a string that might include a display name."""
        try:
            # Handle format like: "Display Name <email@example.com>"
            if '<' in address_string and '>' in address_string:
                return address_string[address_string.find('<')+1:address_string.find('>')]
            # Handle format with just email address
            return address_string.strip()
        except Exception as e:
            log_error(api_logger, e, f"Failed to extract email from: {address_string}")
            return None

    def _parse_message(self, message):
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract clean email address from from_header
            from_email = self._extract_email(from_header)
            if not from_email:
                from_email = from_header

            # Extract body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                        break
            elif 'body' in message['payload']:
                body = base64.urlsafe_b64decode(message['payload']['body'].get('data', '')).decode('utf-8')

            # Ensure threadId is included and not null
            thread_id = message.get('threadId')
            if not thread_id:
                api_logger.warning(f"No threadId found for message {message.get('id', 'unknown')}")
                thread_id = message.get('id')  # Use message ID as fallback

            return {
                'id': message['id'],
                'threadId': thread_id,
                'subject': subject,
                'from': from_header,  # Keep original for display
                'from_email': from_email,  # Add clean email for reply
                'date': date_header,
                'snippet': message.get('snippet', ''),
                'body': body
            }
        except Exception as e:
            log_error(api_logger, e, f"Failed to parse email message ID: {message.get('id', 'unknown')}")
            return None

    def send_email(self, to, subject, body, thread_id=None):
        try:
            message = {
                'raw': base64.urlsafe_b64encode(
                    self._create_message(to, subject, body, thread_id)
                    .encode('utf-8')
                ).decode('utf-8')
            }
            
            if thread_id:
                message['threadId'] = thread_id
                
            api_logger.info(f"Sending email reply to thread: {thread_id}")
            try:
                sent_message = self.service.users().messages().send(
                    userId='me',
                    body=message
                ).execute()
                api_logger.info("Email sent successfully")
                return sent_message
            except Exception as e:
                error_msg = str(e)
                if 'insufficient authentication scopes' in error_msg.lower():
                    api_logger.error("Insufficient Gmail permissions - user needs to re-authenticate")
                    raise Exception("Additional permissions required. Please log out and sign in again to grant email sending permission.")
                raise
        except Exception as e:
            log_error(api_logger, e, "Failed to send email")
            raise

    def _create_message(self, to, subject, body, thread_id=None):
        """Create email message in RFC 822 format"""
        message = email.message.EmailMessage()
        message.set_content(body)
        message['to'] = to
        message['subject'] = subject
        
        if thread_id:
            message['References'] = f'<{thread_id}>'
            message['In-Reply-To'] = f'<{thread_id}>'
            
        return message.as_string()

    def get_thread(self, thread_id):
        """Get full email thread details"""
        try:
            api_logger.info(f"Fetching thread: {thread_id}")
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            # Parse the thread messages
            messages = []
            for msg in thread.get('messages', []):
                parsed_msg = self._parse_message(msg)
                if parsed_msg:
                    messages.append(parsed_msg)
                    
            return {
                'id': thread['id'],
                'messages': messages,
                'snippet': thread.get('snippet', '')
            }
        except Exception as e:
            log_error(api_logger, e, f"Failed to fetch thread: {thread_id}")
            raise