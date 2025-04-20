from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GmailService:
    def __init__(self, credentials_dict):
        self.credentials = Credentials.from_authorized_user_info(credentials_dict)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def get_today_emails(self):
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = f'after:{int(start_of_day.timestamp())}'
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()

            messages = results.get('messages', [])
            return [self._get_email_details(msg['id']) for msg in messages]
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def _get_email_details(self, msg_id):
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Get email body
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                body = self._get_text_from_parts(parts)
            else:
                data = message['payload'].get('body', {}).get('data', '')
                body = base64.urlsafe_b64decode(data).decode() if data else ''

            return {
                'id': msg_id,
                'threadId': message['threadId'],
                'subject': subject,
                'from': from_header,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body': body
            }

        except Exception as e:
            print(f"Error fetching email details for {msg_id}: {e}")
            return None

    def _get_text_from_parts(self, parts):
        text = []
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    text.append(base64.urlsafe_b64decode(data).decode())
            elif 'parts' in part:
                text.extend(self._get_text_from_parts(part['parts']))
        return '\n'.join(text)