"""
Notification models for the consultation system.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Notification type choices."""
    EMAIL = 'EMAIL', 'Email'
    IN_APP = 'IN_APP', 'In-App'


class MessageType(models.TextChoices):
    """Message type choices."""
    BOOKING_CREATED = 'BOOKING_CREATED', 'Booking Created'
    BOOKING_CONFIRMED = 'BOOKING_CONFIRMED', 'Booking Confirmed'
    REMINDER_24H = 'REMINDER_24H', '24-Hour Reminder'
    CANCELLED = 'CANCELLED', 'Cancelled'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'


class EmailStatus(models.TextChoices):
    """Email status choices."""
    PENDING = 'PENDING', 'Pending'
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'


class Notification(models.Model):
    """
    Notification model for user notifications.
    
    Attributes:
        user: Foreign key to User who receives the notification
        consultation: Foreign key to related Consultation
        notification_type: Type of notification (EMAIL, IN_APP)
        message_type: Type of message/event
        sent_at: When notification was sent
        read_at: When notification was read (for in-app notifications)
        email_status: Status of email delivery (PENDING, SENT, FAILED)
        created_at: Record creation timestamp
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives the notification"
    )
    consultation = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Related consultation (if applicable)"
    )
    notification_type = models.CharField(
        max_length=10,
        choices=NotificationType.choices,
        help_text="Type of notification"
    )
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        help_text="Type of message/event"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read (for in-app notifications)"
    )
    email_status = models.CharField(
        max_length=10,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        help_text="Status of email delivery"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['consultation']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['email_status']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"{self.message_type} - {self.user.email} ({self.notification_type})"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read_at and self.notification_type == NotificationType.IN_APP:
            self.read_at = timezone.now()
            self.save()
            return True
        return False
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        if not self.sent_at:
            self.sent_at = timezone.now()
            self.email_status = EmailStatus.SENT
            self.save()
            return True
        return False
    
    def mark_as_failed(self):
        """Mark notification as failed."""
        self.email_status = EmailStatus.FAILED
        self.save()
        return True
    
    def is_read(self):
        """Check if notification is read."""
        return self.read_at is not None

