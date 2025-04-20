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

    def get_recent_emails(self, max_results=10):
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

    def _parse_message(self, message):
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                        break
            elif 'body' in message['payload']:
                body = base64.urlsafe_b64decode(message['payload']['body'].get('data', '')).decode('utf-8')

            return {
                'id': message['id'],
                'threadId': message['threadId'],
                'subject': subject,
                'from': from_header,
                'date': date_header,
                'snippet': message.get('snippet', ''),
                'body': body
            }
        except Exception as e:
            log_error(api_logger, e, f"Failed to parse email message ID: {message.get('id', 'unknown')}")
            return None