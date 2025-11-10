from django.shortcuts import render
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import ConsultationSlot, Booking, ConsultationNote
from .serializers import ConsultationSlotSerializer, BookingSerializer, ConsultationNoteSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProfessor, IsStudent
from .google_calendar import get_google_auth_flow, get_calendar_service
from notifications.task import send_booking_confirmation_email, send_booking_notification_to_professor, send_cancellation_email

# Create your views here.
class ConsultationSlotViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSlotSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsProfessor()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = ConsultationSlot.objects.all()
        
        # Filter by professor
        professor_id = self.request.query_params.get('professor_id')
        if professor_id:
            queryset = queryset.filter(professor_id=professor_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)
        
        # Only show future slots by default
        if not self.request.query_params.get('include_past'):
            queryset = queryset.filter(start_time__gte=timezone.now())
        
        return queryset.select_related('professor')
    
    def perform_create(self, serializer):
        serializer.save(professor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_slots(self, request):
        """Get consultation slots created by the logged-in professor"""
        if request.user.user_type != 'professor':
            return Response(
                {'error': 'Only professors can view their slots'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        slots = ConsultationSlot.objects.filter(professor=request.user)
        page = self.paginate_queryset(slots)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(slots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a consultation slot"""
        slot = self.get_object()
        
        if slot.professor != request.user:
            return Response(
                {'error': 'You can only cancel your own slots'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        slot.status = 'cancelled'
        slot.save()
        
        # Cancel all bookings for this slot
        slot.bookings.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        
        return Response({'message': 'Slot cancelled successfully'})

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'student':
            # Students see their own bookings
            queryset = Booking.objects.filter(student=user)
        elif user.user_type == 'professor':
            # Professors see bookings for their slots
            queryset = Booking.objects.filter(slot__professor=user)
        else:
            queryset = Booking.objects.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('slot', 'student', 'slot__professor')
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Professor confirms a booking"""
        booking = self.get_object()
        
        if booking.slot.professor != request.user:
            return Response(
                {'error': 'Only the professor can confirm this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        # Update slot status if needed
        if booking.slot.status == 'available':
            booking.slot.status = 'booked'
            booking.slot.save()
        
        return Response({'message': 'Booking confirmed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        # Both student and professor can cancel
        if booking.student != request.user and booking.slot.professor != request.user:
            return Response(
                {'error': 'You cannot cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # Update slot status if no more active bookings
        active_bookings = booking.slot.bookings.filter(
            status__in=['pending', 'confirmed']
        ).count()
        if active_bookings == 0:
            booking.slot.status = 'available'
            booking.slot.save()
        
        return Response({'message': 'Booking cancelled'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark booking as completed"""
        booking = self.get_object()
        
        if booking.slot.professor != request.user:
            return Response(
                {'error': 'Only the professor can mark this as completed'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'completed'
        booking.save()
        
        booking.slot.status = 'completed'
        booking.slot.save()
        
        return Response({'message': 'Booking marked as completed'})

class ConsultationNoteViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'professor':
            return ConsultationNote.objects.filter(booking__slot__professor=user)
        elif user.user_type == 'student':
            return ConsultationNote.objects.filter(booking__student=user)
        
        return ConsultationNote.objects.none()
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_auth(request):
    """Initiate Google Calendar OAuth flow"""
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    request.session['google_auth_state'] = state
    return Response({'auth_url': authorization_url})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_callback(request):
    """Handle Google Calendar OAuth callback"""
    state = request.session.get('google_auth_state')
    flow = get_google_auth_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    credentials = flow.credentials
    request.user.profile.google_calendar_token = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    request.user.profile.save()
    
    return Response({'message': 'Google Calendar connected successfully'})