from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class ConsultationSlot(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consulation_slots',
        limit_choices_to={'user_type': 'professor'}
    )
    title = models.CharField(max_length=200, default="Consultation")
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    max_students = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['professor', 'start_time']),
            models.Index(fields=['status', 'start_time']),
        ]
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after the start time")
        if self.start_time < timezone.now():
            raise ValidationError("Cannot create slots in the past")
        
    def __str__(self):
        return f"{self.professor.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No_Show'),
    )
    slot = models.ForeignKey(ConsultationSlot, on_delete=models.CASCADE, related_name='bookings')
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings', limit_choices_to={'user_type': 'student'})

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(help_text="Reason for consultation")
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['slot', 'student']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['slot', 'status']),
        ]

    def clean(self):
        if self.slot.status == 'booked' and self.slot.bookings.filter(status__in=['pending', 'confirmed']).count() >= self.slot.max_students:
            raise ValidationError("This slot is fully booked")

    def __str__(self):
        return f"{self.student.username} - {self.slot}"

class ConsultationNote(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='consultation_note'
    )
    professor_notes = models.TextField(help_text="Professor's notes about the consultation")
    student_feedback = models.TextField(blank=True, help_text="Student's feedback")
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rating from 1-5"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notes for {self.booking}"
