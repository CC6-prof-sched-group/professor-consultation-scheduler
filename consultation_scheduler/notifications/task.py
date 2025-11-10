from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def send_booking_confirmation_email(booking_id):
    """Send confirmation email when a booking is created"""
    from consultations.models import Booking
    
    try:
        booking = Booking.objects.select_related('slot', 'student', 'slot__professor').get(id=booking_id)
        
        subject = f'Consultation Booking Confirmation - {booking.slot.title}'
        
        context = {
            'student_name': booking.student.get_full_name() or booking.student.username,
            'professor_name': booking.slot.professor.get_full_name() or booking.slot.professor.username,
            'slot_title': booking.slot.title,
            'start_time': booking.slot.start_time,
            'end_time': booking.slot.end_time,
            'location': booking.slot.location,
            'is_online': booking.slot.is_online,
            'meeting_link': booking.slot.meeting_link,
            'reason': booking.reason,
        }
        
        html_message = render_to_string('emails/booking_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.student.email],
            html_message=html_message,
        )
        
        return f"Confirmation email sent to {booking.student.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_booking_notification_to_professor(booking_id):
    """Notify professor about new booking"""
    from consultations.models import Booking
    
    try:
        booking = Booking.objects.select_related('slot', 'student', 'slot__professor').get(id=booking_id)
        
        subject = f'New Consultation Booking - {booking.slot.title}'
        
        context = {
            'professor_name': booking.slot.professor.get_full_name() or booking.slot.professor.username,
            'student_name': booking.student.get_full_name() or booking.student.username,
            'student_email': booking.student.email,
            'slot_title': booking.slot.title,
            'start_time': booking.slot.start_time,
            'end_time': booking.slot.end_time,
            'reason': booking.reason,
            'notes': booking.notes,
        }
        
        html_message = render_to_string('emails/booking_notification_professor.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.slot.professor.email],
            html_message=html_message,
        )
        
        return f"Notification sent to professor {booking.slot.professor.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_booking_reminder(booking_id):
    """Send reminder email before consultation"""
    from consultations.models import Booking
    
    try:
        booking = Booking.objects.select_related('slot', 'student', 'slot__professor').get(id=booking_id)
        
        subject = f'Reminder: Upcoming Consultation - {booking.slot.title}'
        
        context = {
            'student_name': booking.student.get_full_name() or booking.student.username,
            'professor_name': booking.slot.professor.get_full_name() or booking.slot.professor.username,
            'slot_title': booking.slot.title,
            'start_time': booking.slot.start_time,
            'end_time': booking.slot.end_time,
            'location': booking.slot.location,
            'is_online': booking.slot.is_online,
            'meeting_link': booking.slot.meeting_link,
        }
        
        html_message = render_to_string('emails/booking_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        # Send to student
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.student.email],
            html_message=html_message,
        )
        
        # Send to professor
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.slot.professor.email],
            html_message=html_message,
        )
        
        return f"Reminder sent to both parties"
    except Exception as e:
        return f"Error sending reminder: {str(e)}"

@shared_task
def send_cancellation_email(booking_id, cancelled_by):
    """Send email when booking is cancelled"""
    from consultations.models import Booking
    
    try:
        booking = Booking.objects.select_related('slot', 'student', 'slot__professor').get(id=booking_id)
        
        subject = f'Consultation Cancelled - {booking.slot.title}'
        
        context = {
            'student_name': booking.student.get_full_name() or booking.student.username,
            'professor_name': booking.slot.professor.get_full_name() or booking.slot.professor.username,
            'slot_title': booking.slot.title,
            'start_time': booking.slot.start_time,
            'cancelled_by': cancelled_by,
        }
        
        html_message = render_to_string('emails/booking_cancellation.html', context)
        plain_message = strip_tags(html_message)
        
        # Send to both parties
        recipients = [booking.student.email, booking.slot.professor.email]
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            html_message=html_message,
        )
        
        return f"Cancellation email sent to both parties"
    except Exception as e:
        return f"Error sending email: {str(e)}"
