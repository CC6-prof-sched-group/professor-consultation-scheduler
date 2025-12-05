from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count
import json


class ProfessorStatus(models.TextChoices):
    """Professor availability status choices."""
    AVAILABLE = 'AVAILABLE', 'Available'
    BUSY = 'BUSY', 'Busy'
    AWAY = 'AWAY', 'Away'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'


class ProfessorProfile(models.Model):
    """
    Professor profile with consultation preferences and availability.
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
    status = models.CharField(
        max_length=20,
        choices=ProfessorStatus.choices,
        default=ProfessorStatus.AVAILABLE,
        help_text="Current availability status"
    )
    
    # NEW: Rating cache fields
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text="Cached average rating"
    )
    total_reviews = models.PositiveIntegerField(
        default=0,
        help_text="Total number of reviews"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'professor_profiles'
        verbose_name = 'Professor Profile'
        verbose_name_plural = 'Professor Profiles'
        ordering = ['-average_rating', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['-average_rating']),
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
    
    # NEW: Rating methods
    def calculate_ratings(self):
        """Calculate and cache average rating and review count."""
        from apps.consultations.models import Consultation
        
        ratings = Consultation.objects.filter(
            professor=self.user,
            rating__isnull=False
        ).aggregate(
            avg_rating=Avg('rating'),
            total=Count('id')
        )
        
        self.average_rating = round(ratings['avg_rating'] or 0, 2)
        self.total_reviews = ratings['total'] or 0
        self.save(update_fields=['average_rating', 'total_reviews', 'updated_at'])
        
        return self.average_rating, self.total_reviews
    
    def get_rating_display(self):
        """Get rating as stars (1-5)."""
        return round(self.average_rating)
    
    def get_rating_percentage(self):
        """Get rating as percentage (0-100)."""
        return (self.average_rating / 5.0) * 100 if self.average_rating else 0