"""
Admin configuration for consultations app.
"""
from django.contrib import admin
from apps.consultations.models import Consultation
from apps.consultations.models import CancellationRecord, RescheduleRequest


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    """Admin interface for Consultation model."""
    list_display = [
        'title', 'student', 'professor', 'scheduled_date', 'scheduled_time',
        'status', 'duration', 'rating', 'created_at'
    ]
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['title', 'description', 'student__email', 'professor__email']
    readonly_fields = ['booking_created_at', 'confirmed_at', 'cancelled_at', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'professor', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration', 'location', 'meeting_link')
        }),
        ('Status', {
            'fields': ('status', 'booking_created_at', 'confirmed_at', 'cancelled_at', 'cancellation_reason')
        }),
        ('Integration', {
            'fields': ('google_calendar_event_id',)
        }),
        ('Feedback', {
            'fields': ('notes', 'rating', 'feedback')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CancellationRecord)
class CancellationRecordAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'requested_by', 'status', 'requested_at', 'processed_by', 'processed_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['consultation__title', 'requested_by__email', 'processed_by__email']


@admin.register(RescheduleRequest)
class RescheduleRequestAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'requested_by', 'new_date', 'new_time', 'status', 'requested_at', 'processed_by']
    list_filter = ['status', 'requested_at', 'new_date']
    search_fields = ['consultation__title', 'requested_by__email', 'processed_by__email']

