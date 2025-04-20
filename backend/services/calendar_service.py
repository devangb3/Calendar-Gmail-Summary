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
            'id': event.get('id'),  # Add event ID
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

    def accept_calendar_invite(self, event_id):
        """Accept a calendar invitation"""
        try:
            api_logger.info(f"Accepting calendar invite for event: {event_id}")
            
            # Get the event first to check if we need to handle it
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Find the attendee that matches the authenticated user
            user_email = self.service.calendarList().get(calendarId='primary').execute().get('id')
            user_attendee = next(
                (attendee for attendee in event.get('attendees', [])
                if attendee.get('email') == user_email),
                None
            )
            
            if not user_attendee:
                api_logger.warning(f"User not found in attendee list for event: {event_id}")
                return False
                
            if user_attendee.get('responseStatus') == 'accepted':
                api_logger.info("Event already accepted")
                return True
                
            # Update the attendee's response status
            user_attendee['responseStatus'] = 'accepted'
            
            # Update the event
            self.service.events().patch(
                calendarId='primary',
                eventId=event_id,
                body={'attendees': event.get('attendees', [])},
                sendUpdates='all'  # Notify other attendees
            ).execute()
            
            api_logger.info(f"Successfully accepted calendar invite for event: {event_id}")
            return True
            
        except Exception as e:
            log_error(api_logger, e, f"Failed to accept calendar invite for event: {event_id}")
            raise
            
    def decline_calendar_invite(self, event_id):
        """Decline a calendar invitation"""
        try:
            api_logger.info(f"Declining calendar invite for event: {event_id}")
            
            # Get the event first to check if we need to handle it
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Find the attendee that matches the authenticated user
            user_email = self.service.calendarList().get(calendarId='primary').execute().get('id')
            user_attendee = next(
                (attendee for attendee in event.get('attendees', [])
                if attendee.get('email') == user_email),
                None
            )
            
            if not user_attendee:
                api_logger.warning(f"User not found in attendee list for event: {event_id}")
                return False
                
            if user_attendee.get('responseStatus') == 'declined':
                api_logger.info("Event already declined")
                return True
                
            # Update the attendee's response status
            user_attendee['responseStatus'] = 'declined'
            
            # Update the event
            self.service.events().patch(
                calendarId='primary',
                eventId=event_id,
                body={'attendees': event.get('attendees', [])},
                sendUpdates='all'  # Notify other attendees
            ).execute()
            
            api_logger.info(f"Successfully declined calendar invite for event: {event_id}")
            return True
            
        except Exception as e:
            log_error(api_logger, e, f"Failed to decline calendar invite for event: {event_id}")
            raise

    def get_pending_invites(self):
        """Get list of pending calendar invitations"""
        try:
            api_logger.info("Fetching pending calendar invites")
            
            # Get user's email
            user_email = self.service.calendarList().get(calendarId='primary').execute().get('id')
            
            # Get events where user's response is needed or not responded
            # Look for future events within next 30 days
            time_min = datetime.now(timezone.utc)
            time_max = time_min + timedelta(days=30)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=20,  # Increased to catch more potential invites
                singleEvents=True,
                orderBy='startTime',
                showDeleted=False,
                fields='items(id,summary,start,end,attendees,location,status,description,htmlLink)'  # Optimize response
            ).execute()
            
            events = events_result.get('items', [])
            pending_invites = []
            
            for event in events:
                # Skip events without attendees (not an invitation)
                if not event.get('attendees'):
                    continue
                    
                # Check if user is an attendee and hasn't responded
                attendees = event.get('attendees', [])
                user_attendee = next(
                    (attendee for attendee in attendees 
                    if attendee.get('email') == user_email and 
                    attendee.get('responseStatus') in ['needsAction', 'tentative']),  # Include tentative responses
                    None
                )
                
                # Only include if user is an attendee who needs to respond
                # and event is not cancelled
                if (user_attendee and 
                    event.get('status') != 'cancelled'):
                    formatted_event = self._format_event(event)
                    formatted_event['responseStatus'] = user_attendee.get('responseStatus', 'needsAction')
                    pending_invites.append(formatted_event)
                    
            api_logger.info(f"Found {len(pending_invites)} pending invites")
            return pending_invites
            
        except Exception as e:
            log_error(api_logger, e, "Failed to fetch pending invites")
            raise