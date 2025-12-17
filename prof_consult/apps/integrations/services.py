"""
Google Calendar integration service.
"""
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user):
        """
        Initialize Google Calendar service for a user.
        
        Args:
            user: User instance with Google OAuth tokens
        """
        self.user = user
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        if not self.user.google_access_token:
            logger.warning(f"User {self.user.email} does not have Google access token.")
            return None
        
        try:
            creds = Credentials(
                token=self.user.get_google_access_token(),
                refresh_token=self.user.get_google_refresh_token(),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
            )
            
            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update user's access token
                self.user.google_access_token = creds.token
                self.user.save()
            
            self.service = build('calendar', 'v3', credentials=creds)
            return self.service
        except Exception as e:
            logger.error(f"Failed to authenticate Google Calendar for user {self.user.email}: {str(e)}")
            return None
    
    def create_event(self, consultation):
        """
        Create a Google Calendar event for a consultation.
        
        Args:
            consultation: Consultation instance
            
        Returns:
            Event ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Google Calendar service not authenticated.")
            return None
        
        try:
            start_datetime = consultation.get_datetime()
            end_datetime = start_datetime + timedelta(minutes=consultation.duration)
            
            event = {
                'summary': f'Consultation: {consultation.title}',
                'description': consultation.description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {'email': consultation.student.email},
                    {'email': consultation.professor.email},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            
            if consultation.location:
                event['location'] = consultation.location
            
            if consultation.meeting_link:
                event['description'] += f'\n\nMeeting Link: {consultation.meeting_link}'
            
            calendar_id = getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary')
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Created Google Calendar event {event['id']} for consultation {consultation.id}")
            return event['id']
        except HttpError as e:
            logger.error(f"Failed to create Google Calendar event: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating Google Calendar event: {str(e)}")
            return None
    
    def update_event(self, consultation):
        """
        Update a Google Calendar event for a consultation.
        
        Args:
            consultation: Consultation instance with google_calendar_event_id
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service or not consultation.google_calendar_event_id:
            return False
        
        try:
            start_datetime = consultation.get_datetime()
            end_datetime = start_datetime + timedelta(minutes=consultation.duration)
            
            event = self.service.events().get(
                calendarId=getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary'),
                eventId=consultation.google_calendar_event_id
            ).execute()
            
            event['summary'] = f'Consultation: {consultation.title}'
            event['description'] = consultation.description
            event['start']['dateTime'] = start_datetime.isoformat()
            event['start']['timeZone'] = 'UTC'
            event['end']['dateTime'] = end_datetime.isoformat()
            event['end']['timeZone'] = 'UTC'
            
            if consultation.location:
                event['location'] = consultation.location
            
            if consultation.meeting_link:
                event['description'] += f'\n\nMeeting Link: {consultation.meeting_link}'
            
            updated_event = self.service.events().update(
                calendarId=getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary'),
                eventId=consultation.google_calendar_event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Updated Google Calendar event {updated_event['id']} for consultation {consultation.id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to update Google Calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Google Calendar event: {str(e)}")
            return False
    
    def delete_event(self, event_id):
        """
        Delete a Google Calendar event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId=getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary'),
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Deleted Google Calendar event {event_id}")
            return True
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Google Calendar event {event_id} not found (already deleted?)")
                return True
            logger.error(f"Failed to delete Google Calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting Google Calendar event: {str(e)}")
            return False

    def get_free_busy_periods(self, start_time, end_time):
        """
        Get free/busy information from Google Calendar.
        
        Args:
            start_time: Start datetime (aware)
            end_time: End datetime (aware)
            
        Returns:
            List of busy periods [{'start': datetime, 'end': datetime}]
        """
        if not self.service:
            return []
            
        try:
            calendar_id = getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary')
            
            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "timeZone": 'UTC',
                "items": [{"id": calendar_id}]
            }
            
            events_result = self.service.freebusy().query(body=body).execute()
            calendars = events_result.get('calendars', {})
            busy_periods = calendars.get(calendar_id, {}).get('busy', [])
            
            # Convert strings to datetime objects
            cleaned_periods = []
            for period in busy_periods:
                # Handle Z suffix for ISO format
                start_str = period['start'].replace('Z', '+00:00')
                end_str = period['end'].replace('Z', '+00:00')
                
                start = datetime.fromisoformat(start_str)
                end = datetime.fromisoformat(end_str)
                cleaned_periods.append({
                    'start': start,
                    'end': end
                })
                
            return cleaned_periods
            
        except HttpError as e:
            logger.error(f"Failed to get free/busy info: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting free/busy info: {str(e)}")
            return []


def get_google_oauth_flow():
    """Get Google OAuth flow for authentication."""
    client_config = {
        "web": {
            "client_id": settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
            "client_secret": settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('redirect_uri', '')]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=GoogleCalendarService.SCOPES,
        redirect_uri=settings.SOCIALACCOUNT_PROVIDERS['google']['APP'].get('redirect_uri', '')
    )
    
    return flow

