from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from consultations.models import Booking
from .tasks import send_booking_reminder

@shared_task
def schedule_reminders():
    """Check for bookings that need reminders (24 hours before)"""
    now = timezone.now()
    reminder_time = now + timedelta(hours=24)
    
    # Get bookings that are 24 hours away
    bookings = Booking.objects.filter(
        status__in=['pending', 'confirmed'],
        slot__start_time__gte=now,
        slot__start_time__lte=reminder_time
    )
    
    for booking in bookings:
        send_booking_reminder.delay(booking.id)
    
    return f"Scheduled {bookings.count()} reminders"