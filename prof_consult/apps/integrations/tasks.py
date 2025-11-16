"""
Celery tasks for Google Calendar integration.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.consultations.models import Consultation, ConsultationStatus
from apps.integrations.services import GoogleCalendarService

logger = logging.getLogger(__name__)


@shared_task
def sync_google_calendar_events():
    """
    Sync consultation status with Google Calendar events.
    Runs periodically via Celery Beat.
    """
    # Get consultations that are confirmed but might have been cancelled in calendar
    consultations = Consultation.objects.filter(
        status=ConsultationStatus.CONFIRMED,
        google_calendar_event_id__isnull=False
    )
    
    synced_count = 0
    for consultation in consultations:
        try:
            # Check if event still exists in Google Calendar
            calendar_service = GoogleCalendarService(consultation.professor)
            if calendar_service.service:
                calendar_id = calendar_service.service.calendarId if hasattr(calendar_service, 'calendarId') else 'primary'
                try:
                    event = calendar_service.service.events().get(
                        calendarId=calendar_id,
                        eventId=consultation.google_calendar_event_id
                    ).execute()
                    
                    # Check if event was cancelled
                    if event.get('status') == 'cancelled':
                        consultation.status = ConsultationStatus.CANCELLED
                        consultation.cancelled_at = timezone.now()
                        consultation.save()
                        synced_count += 1
                        logger.info(f"Synced consultation {consultation.id} - marked as cancelled")
                except Exception as e:
                    if '404' in str(e):
                        # Event was deleted
                        consultation.status = ConsultationStatus.CANCELLED
                        consultation.cancelled_at = timezone.now()
                        consultation.save()
                        synced_count += 1
                        logger.info(f"Synced consultation {consultation.id} - event deleted")
        except Exception as e:
            logger.error(f"Error syncing consultation {consultation.id}: {str(e)}")
    
    logger.info(f"Synced {synced_count} consultations with Google Calendar")

