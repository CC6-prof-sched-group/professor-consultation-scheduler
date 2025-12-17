"""
Service layer for consultation business logic.
Centralizes DB updates, Google Calendar sync, and Notifications.
"""
import logging
from django.utils import timezone
from apps.consultations.models import Consultation, ConsultationStatus
from apps.integrations.services import GoogleCalendarService
from apps.notifications.tasks import (
    send_booking_confirmed_notification,
    send_booking_cancelled_notification,
    send_booking_rescheduled_notification,
    send_reschedule_proposal_notification
)

logger = logging.getLogger(__name__)

class ConsultationService:
    """
    Service for handling consultation lifecycle events.
    """
    
    @staticmethod
    def confirm_consultation(consultation):
        """
        Confirm a consultation.
        Syncs with Google Calendar and sends notifications.
        """
        # 1. Update DB
        consultation.status = ConsultationStatus.CONFIRMED
        consultation.confirmed_at = timezone.now()
        consultation.save()
        
        # 2. Sync with Google Calendar
        try:
            calendar_service = GoogleCalendarService(consultation.professor)
            event_id = calendar_service.create_event(consultation)
            if event_id:
                consultation.google_calendar_event_id = event_id
                consultation.save()
        except Exception as e:
            logger.error(f"Failed to sync with Google Calendar for consultation {consultation.id}: {str(e)}")
            # Don't fail the transaction, just log it.
            
        # 3. Send Notifications
        send_booking_confirmed_notification(consultation.id)
        
        return consultation

    @staticmethod
    def cancel_consultation(consultation, reason, cancelled_by_user=None):
        """
        Cancel a consultation.
        Syncs with Google Calendar and sends notifications.
        """
        # 1. Update DB
        consultation.status = ConsultationStatus.CANCELLED
        consultation.cancelled_at = timezone.now()
        consultation.cancellation_reason = reason
        consultation.save()
        
        # 2. Sync with Google Calendar (Delete Event)
        try:
            if consultation.google_calendar_event_id:
                calendar_service = GoogleCalendarService(consultation.professor)
                calendar_service.delete_event(consultation.google_calendar_event_id)
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event for consultation {consultation.id}: {str(e)}")
            
        # 3. Send Notifications
        send_booking_cancelled_notification(consultation.id, reason)
        
        return consultation

    @staticmethod
    def propose_reschedule(consultation, new_time=None, new_date=None):
        """
        Propose a reschedule (Professor -> Student).
        Does NOT update Google Calendar yet (wait for confirmation).
        """
        # 1. Update DB
        consultation.status = ConsultationStatus.RESCHEDULE_PROPOSED
        if new_time:
            consultation.scheduled_time = new_time
        if new_date:
            consultation.scheduled_date = new_date
        consultation.save()
        
        # 2. Send Notifications
        send_reschedule_proposal_notification(consultation.id)
        
        return consultation

    @staticmethod
    def accept_reschedule(consultation):
        """
        Student accepts reschedule proposal.
        Becomes CONFIRMED. Syncs GCal.
        """
        # 1. Update DB
        consultation.status = ConsultationStatus.CONFIRMED
        consultation.confirmed_at = timezone.now()
        consultation.save()
        
        # 2. Sync with Google Calendar (Update Event if exists, else Create)
        try:
            calendar_service = GoogleCalendarService(consultation.professor)
            if consultation.google_calendar_event_id:
                calendar_service.update_event(consultation)
            else:
                event_id = calendar_service.create_event(consultation)
                if event_id:
                    consultation.google_calendar_event_id = event_id
                    consultation.save()
        except Exception as e:
            logger.error(f"Failed to sync reschedule with Google Calendar for consultation {consultation.id}: {str(e)}")
            
        # 3. Send Notifications (using Rescheduled template)
        send_booking_rescheduled_notification(consultation.id)
        
        return consultation
    
    @staticmethod
    def reschedule_confirmed(consultation, new_date, new_time, new_duration=None):
        """
        Directly reschedule a confirmed consultation (e.g. via API if allowed).
        Usually goes through proposal flow, but if API allows direct change:
        """
        # Update DB
        consultation.scheduled_date = new_date or consultation.scheduled_date
        consultation.scheduled_time = new_time or consultation.scheduled_time
        if new_duration:
            consultation.duration = new_duration
        consultation.status = ConsultationStatus.PENDING # Reset to pending? Or keep confirmed?
        # If forcing reschedule (e.g. admin/professor direct edit), usually keeps confirmed or goes to pending.
        # Let's assume standard flow uses propose_reschedule.
        # This method might be for 'update' action in API.
        
        # For now, let's stick to the flows we know.
        pass
