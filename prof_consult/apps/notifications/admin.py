"""
Admin configuration for notifications app.
"""
from django.contrib import admin
from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""
    list_display = [
        'user', 'message_type', 'notification_type', 'email_status',
        'sent_at', 'read_at', 'created_at'
    ]
    list_filter = ['notification_type', 'message_type', 'email_status', 'created_at']
    search_fields = ['user__email', 'consultation__title']
    readonly_fields = ['sent_at', 'read_at', 'created_at']
    date_hierarchy = 'created_at'

