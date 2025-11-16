"""
Views for notifications app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from django.utils import timezone


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Notification model (read-only, except mark as read).
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return notifications for current user."""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        
        if notification.user != request.user:
            return Response(
                {'error': 'You can only mark your own notifications as read.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        notifications = self.get_queryset().filter(read_at__isnull=True)
        updated = notifications.update(read_at=timezone.now())
        return Response({'message': f'{updated} notifications marked as read.'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(read_at__isnull=True).count()
        return Response({'unread_count': count})

