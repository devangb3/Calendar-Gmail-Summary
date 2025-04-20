from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class CalendarService:
    def __init__(self, credentials_dict):
        self.credentials = Credentials.from_authorized_user_info(credentials_dict)
        self.service = build('calendar', 'v3', credentials=self.credentials)

    def get_today_events(self):
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return [self._format_event(event) for event in events]

    def _format_event(self, event):
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
        end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
        
        return {
            'summary': event.get('summary', 'No Title'),
            'start': start,
            'end': end,
            'description': event.get('description', ''),
            'attendees': [
                {'email': attendee.get('email'), 'name': attendee.get('displayName')}
                for attendee in event.get('attendees', [])
            ],
            'location': event.get('location', ''),
            'status': event.get('status', ''),
            'htmlLink': event.get('htmlLink', '')
        }