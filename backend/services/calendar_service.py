from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from utils.logger import api_logger, log_error

class CalendarService:
    def __init__(self, credentials_dict):
        try:
            api_logger.info("Initializing Calendar service")
            credentials = Credentials(
                token=credentials_dict['token'],
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict['token_uri'],
                client_id=credentials_dict['client_id'],
                client_secret=credentials_dict['client_secret'],
                scopes=credentials_dict['scopes']
            )
            self.service = build('calendar', 'v3', credentials=credentials)
            api_logger.info("Calendar service initialized successfully")
        except Exception as e:
            log_error(api_logger, e, "Failed to initialize Calendar service")
            raise

    def get_events(self, time_min=None, time_max=None, max_results=10):
        try:
            api_logger.info("Fetching calendar events", 
                          extra={"time_min": time_min, "time_max": time_max, "max_results": max_results})
            
            now = datetime.now(timezone.utc)
            if not time_min:
                # Format time as RFC3339 timestamp
                time_min = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            if not time_max:
                # Format time as RFC3339 timestamp, 7 days from now
                time_max = (now + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            api_logger.info(f"Successfully fetched {len(events)} calendar events")
            return [self._format_event(event) for event in events]
            
        except Exception as e:
            log_error(api_logger, e, "Failed to fetch calendar events")
            raise

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