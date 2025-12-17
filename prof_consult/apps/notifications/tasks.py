"""
Notification functions for the notification system.
"""
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from apps.notifications.models import Notification, NotificationType, MessageType, EmailStatus
from apps.consultations.models import Consultation, ConsultationStatus
from apps.integrations.services import GoogleCalendarService

logger = logging.getLogger(__name__)


def send_booking_created_notification(consultation_id):
    """
    Send notifications when a booking is created.
    
    Args:
        consultation_id: ID of the consultation
    """
    try:
        consultation = Consultation.objects.get(id=consultation_id)
    except Consultation.DoesNotExist:
        logger.error(f"Consultation {consultation_id} does not exist.")
        return
    
    # Notify student
    student_notification = Notification.objects.create(
        user=consultation.student,
        consultation=consultation,
        notification_type=NotificationType.IN_APP,
        message_type=MessageType.BOOKING_CREATED
    )
    
    # Notify professor
    professor_notification = Notification.objects.create(
        user=consultation.professor,
        consultation=consultation,
        notification_type=NotificationType.IN_APP,
        message_type=MessageType.BOOKING_CREATED
    )
    
    # Send email to student
    send_email_notification(student_notification.id)
    
    # Send email to professor
    send_email_notification(professor_notification.id)
    
    logger.info(f"Created notifications for consultation {consultation_id}")


def send_booking_confirmed_notification(consultation_id):
    """
    Send notifications when a booking is confirmed.
    
    Args:
        consultation_id: ID of the consultation
    """
    try:
        consultation = Consultation.objects.get(id=consultation_id)
    except Consultation.DoesNotExist:
        logger.error(f"Consultation {consultation_id} does not exist.")
        return
    
    # Notify student
    notification = Notification.objects.create(
        user=consultation.student,
        consultation=consultation,
        notification_type=NotificationType.IN_APP,
        message_type=MessageType.BOOKING_CONFIRMED
    )
    
    # Send email
    send_email_notification(notification.id)
    
    logger.info(f"Sent confirmation notification for consultation {consultation_id}")


def send_booking_cancelled_notification(consultation_id, reason=''):
    """
    Send notifications when a booking is cancelled.
    
    Args:
        consultation_id: ID of the consultation
        reason: Reason for cancellation
    """
    try:
        consultation = Consultation.objects.get(id=consultation_id)
    except Consultation.DoesNotExist:
        logger.error(f"Consultation {consultation_id} does not exist.")
        return
    
    # Notify both parties
    for user in [consultation.student, consultation.professor]:
        notification = Notification.objects.create(
            user=user,
            consultation=consultation,
            notification_type=NotificationType.IN_APP,
            message_type=MessageType.CANCELLED
        )
        send_email_notification(notification.id, extra_context={'reason': reason})
    
    logger.info(f"Sent cancellation notifications for consultation {consultation_id}")


def send_booking_rescheduled_notification(consultation_id):
    """
    Send notifications when a booking is rescheduled.
    
    Args:
        consultation_id: ID of the consultation
    """
    try:
        consultation = Consultation.objects.get(id=consultation_id)
    except Consultation.DoesNotExist:
        logger.error(f"Consultation {consultation_id} does not exist.")
        return
    
    # Notify both parties
    for user in [consultation.student, consultation.professor]:
        notification = Notification.objects.create(
            user=user,
            consultation=consultation,
            notification_type=NotificationType.IN_APP,
            message_type=MessageType.RESCHEDULED
        )
        send_email_notification(notification.id)
    
    logger.info(f"Sent reschedule notifications for consultation {consultation_id}")


def send_email_notification(notification_id, extra_context=None):
    """
    Send email notification.
    
    Args:
        notification_id: ID of the notification
        extra_context: Additional context for email template
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} does not exist.")
        return
    
    if notification.notification_type != NotificationType.EMAIL:
        # Also send email for in-app notifications
        pass
    
    try:
        consultation = notification.consultation
        user = notification.user
        
        # Prepare email context
        context = {
            'user': user,
            'consultation': consultation,
            'message_type': notification.message_type,
            'site_name': getattr(settings, 'SITE_NAME', 'Consultation System'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        if extra_context:
            context.update(extra_context)
        
        # Get email template based on message type
        template_map = {
            MessageType.BOOKING_CREATED: 'emails/booking_created.html',
            MessageType.BOOKING_CONFIRMED: 'emails/booking_confirmed.html',
            MessageType.REMINDER_24H: 'emails/reminder_24h.html',
            MessageType.CANCELLED: 'emails/booking_cancelled.html',
            MessageType.RESCHEDULED: 'emails/booking_rescheduled.html',
        }
        
        template_name = template_map.get(notification.message_type, 'emails/notification.html')
        subject_map = {
            MessageType.BOOKING_CREATED: 'New Consultation Booking',
            MessageType.BOOKING_CONFIRMED: 'Consultation Confirmed',
            MessageType.REMINDER_24H: 'Reminder: Consultation Tomorrow',
            MessageType.CANCELLED: 'Consultation Cancelled',
            MessageType.RESCHEDULED: 'Consultation Rescheduled',
        }
        
        subject = subject_map.get(notification.message_type, 'Consultation Notification')
        
        # Render email
        html_message = render_to_string(template_name, context)
        plain_message = render_to_string(template_name.replace('.html', '.txt'), context)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark as sent
        notification.mark_as_sent()
        
        logger.info(f"Sent email notification {notification_id} to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send email notification {notification_id}: {str(e)}")
        notification.mark_as_failed()


def send_24h_reminders():
    """
    Send 24-hour reminders for upcoming consultations.
    Runs periodically via Celery Beat.
    """
    tomorrow = timezone.now() + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)
    
    consultations = Consultation.objects.filter(
        scheduled_date=tomorrow.date(),
        status__in=[ConsultationStatus.CONFIRMED],
        scheduled_time__gte=tomorrow_start.time(),
        scheduled_time__lt=tomorrow_end.time()
    )
    
    for consultation in consultations:
        # Create notification for both parties
        for user in [consultation.student, consultation.professor]:
            notification, created = Notification.objects.get_or_create(
                user=user,
                consultation=consultation,
                message_type=MessageType.REMINDER_24H,
                defaults={
                    'notification_type': NotificationType.IN_APP,
                }
            )
            
            if created:
                send_email_notification(notification.id)
    
    logger.info(f"Sent 24-hour reminders for {consultations.count()} consultations")

