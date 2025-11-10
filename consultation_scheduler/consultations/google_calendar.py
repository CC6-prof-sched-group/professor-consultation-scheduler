from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
import json

def get_google_auth_flow():
    """Create OAuth2 flow for Google Calendar"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
    return flow

def get_calendar_service(user):
    """Get Google Calendar service for a user"""
    if not user.profile.google_calendar_token:
        return None
    
    credentials = Credentials.from_authorized_user_info(
        user.profile.google_calendar_token
    )
    
    service = build('calendar', 'v3', credentials=credentials)
    return service

def create_calendar_event(slot, service):
    """Create a Google Calendar event for a consultation slot"""
    event = {
        'summary': slot.title,
        'description': slot.description,
        'location': slot.location if not slot.is_online else 'Online',
        'start': {
            'dateTime': slot.start_time.isoformat(),
            'timeZone': 'Asia/Manila',
        },
        'end': {
            'dateTime': slot.end_time.isoformat(),
            'timeZone': 'Asia/Manila',
        },
    }
    
    if slot.meeting_link:
        event['description'] += f"\n\nMeeting Link: {slot.meeting_link}"
    
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event['id']

def update_calendar_event(slot, service):
    """Update a Google Calendar event"""
    if not slot.google_event_id:
        return None
    
    event = {
        'summary': slot.title,
        'description': slot.description,
        'location': slot.location if not slot.is_online else 'Online',
        'start': {
            'dateTime': slot.start_time.isoformat(),
            'timeZone': 'Asia/Manila',
        },
        'end': {
            'dateTime': slot.end_time.isoformat(),
            'timeZone': 'Asia/Manila',
        },
    }
    
    updated_event = service.events().update(
        calendarId='primary',
        eventId=slot.google_event_id,
        body=event
    ).execute()
    return updated_event['id']

def delete_calendar_event(slot, service):
    """Delete a Google Calendar event"""
    if not slot.google_event_id:
        return
    
    service.events().delete(
        calendarId='primary',
        eventId=slot.google_event_id
    ).execute()