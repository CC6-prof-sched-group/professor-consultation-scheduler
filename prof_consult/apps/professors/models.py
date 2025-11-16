"""
Professor profile models for consultation scheduling.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class ProfessorProfile(models.Model):
    """
    Professor profile with consultation preferences and availability.
    
    Attributes:
        user: One-to-one relationship with User model
        title: Professor title (Dr., Prof., etc.)
        department: Professor's department
        office_location: Office location for consultations
        consultation_duration_default: Default consultation duration in minutes
        available_days: JSON field with day/time slots for availability
        max_advance_booking_days: Maximum days in advance students can book
        buffer_time_between_consultations: Buffer time between consultations in minutes
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_profile',
        help_text="Associated user account"
    )
    title = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Professor title (Dr., Prof., etc.)"
    )
    department = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Professor's department"
    )
    office_location = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Office location for consultations"
    )
    consultation_duration_default = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        help_text="Default consultation duration in minutes (15-240)"
    )
    available_days = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON field with day/time slots for availability"
    )
    max_advance_booking_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Maximum days in advance students can book (1-365)"
    )
    buffer_time_between_consultations = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(0), MaxValueValidator(120)],
        help_text="Buffer time between consultations in minutes (0-120)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'professor_profiles'
        verbose_name = 'Professor Profile'
        verbose_name_plural = 'Professor Profiles'
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        title = f"{self.title} " if self.title else ""
        return f"{title}{self.user.get_full_name() or self.user.email}"
    
    def get_available_slots(self, day_of_week):
        """Get available time slots for a specific day of week."""
        if not self.available_days:
            return []
        day_name = day_of_week.lower() if isinstance(day_of_week, str) else day_of_week
        return self.available_days.get(day_name, [])
    
    def set_available_slots(self, day_of_week, slots):
        """Set available time slots for a specific day of week."""
        if not self.available_days:
            self.available_days = {}
        day_name = day_of_week.lower() if isinstance(day_of_week, str) else day_of_week
        self.available_days[day_name] = slots
        self.save()
    
    def get_full_name(self):
        """Get professor's full name."""
        return self.user.get_full_name() or self.user.email

