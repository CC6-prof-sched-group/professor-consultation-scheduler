"""
Serializers for notifications app.
"""
from rest_framework import serializers
from apps.notifications.models import Notification, NotificationType, MessageType, EmailStatus


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    email_status_display = serializers.CharField(source='get_email_status_display', read_only=True)
    consultation_title = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'consultation', 'notification_type',
            'notification_type_display', 'message_type', 'message_type_display',
            'sent_at', 'read_at', 'email_status', 'email_status_display',
            'created_at', 'consultation_title', 'is_read'
        ]
        read_only_fields = [
            'id', 'user', 'sent_at', 'read_at', 'email_status', 'created_at'
        ]
    
    def get_consultation_title(self, obj):
        """Get consultation title if available."""
        return obj.consultation.title if obj.consultation else None
    
    def get_is_read(self, obj):
        """Check if notification is read."""
        return obj.is_read()

