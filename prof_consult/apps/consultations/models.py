"""
Consultation models for booking system.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ConsultationStatus(models.TextChoices):
    """Consultation status choices."""
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    COMPLETED = 'COMPLETED', 'Completed'
    NO_SHOW = 'NO_SHOW', 'No Show'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'


class Consultation(models.Model):
    """
    Consultation booking model.
    
    Attributes:
        student: Foreign key to User (student)
        professor: Foreign key to User (professor)
        title: Consultation title
        description: Consultation description
        scheduled_date: Scheduled date
        scheduled_time: Scheduled time
        duration: Duration in minutes
        status: Current status of consultation
        booking_created_at: When booking was created
        confirmed_at: When consultation was confirmed
        cancelled_at: When consultation was cancelled
        cancellation_reason: Reason for cancellation
        google_calendar_event_id: Google Calendar event ID
        meeting_link: Optional meeting link (for online consultations)
        location: Consultation location
        notes: Professor notes after consultation
        rating: Student rating (1-5) after completion
        feedback: Student feedback after completion
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_consultations',
        help_text="Student who booked the consultation"
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_consultations',
        help_text="Professor providing the consultation"
    )
    title = models.CharField(
        max_length=200,
        help_text="Consultation title"
    )
    description = models.TextField(
        help_text="Consultation description/details"
    )
    scheduled_date = models.DateField(
        help_text="Scheduled date for consultation"
    )
    scheduled_time = models.TimeField(
        help_text="Scheduled time for consultation"
    )
    duration = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        help_text="Duration in minutes (15-240)"
    )
    status = models.CharField(
        max_length=20,
        choices=ConsultationStatus.choices,
        default=ConsultationStatus.PENDING,
        help_text="Current status of consultation"
    )
    booking_created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When booking was created"
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consultation was confirmed by professor"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When consultation was cancelled"
    )
    cancellation_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for cancellation"
    )
    google_calendar_event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Google Calendar event ID"
    )
    meeting_link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Optional meeting link (for online consultations)"
    )
    location = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Consultation location"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Professor notes after consultation"
    )
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Student rating (1-5) after completion"
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        help_text="Student feedback after completion"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consultations'
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['professor']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date', 'scheduled_time']),
            models.Index(fields=['google_calendar_event_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.student.email} with {self.professor.email} ({self.status})"
    
    def get_datetime(self):
        """Get combined scheduled date and time as datetime."""
        from django.utils.dateparse import parse_datetime
        return timezone.make_aware(
            timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
        )
    
    def is_past(self):
        """Check if consultation is in the past."""
        return self.get_datetime() < timezone.now()
    
    def is_upcoming(self):
        """Check if consultation is upcoming."""
        return not self.is_past() and self.status in [
            ConsultationStatus.PENDING,
            ConsultationStatus.CONFIRMED
        ]
    
    def can_be_rated(self):
        """Check if consultation can be rated by student."""
        return self.status == ConsultationStatus.COMPLETED and not self.rating
    
    def can_be_cancelled(self):
        """Check if consultation can be cancelled."""
        return self.status in [
            ConsultationStatus.PENDING,
            ConsultationStatus.CONFIRMED
        ]
    
    def confirm(self):
        """Mark consultation as confirmed."""
        if self.status == ConsultationStatus.PENDING:
            self.status = ConsultationStatus.CONFIRMED
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False
    
    def cancel(self, reason=None):
        """Cancel the consultation."""
        if self.can_be_cancelled():
            self.status = ConsultationStatus.CANCELLED
            self.cancelled_at = timezone.now()
            if reason:
                self.cancellation_reason = reason
            self.save()
            return True
        return False
    
    def complete(self):
        """Mark consultation as completed."""
        if self.status == ConsultationStatus.CONFIRMED:
            self.status = ConsultationStatus.COMPLETED
            self.save()
            return True
        return False
    
    def mark_no_show(self):
        """Mark consultation as no-show."""
        if self.status == ConsultationStatus.CONFIRMED:
            self.status = ConsultationStatus.NO_SHOW
            self.save()
            return True
        return False
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)

