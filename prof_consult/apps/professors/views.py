"""
Views for professors app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta, datetime as dt

from apps.professors.models import ProfessorProfile
from apps.professors.serializers import (
    ProfessorProfileSerializer, ProfessorProfileDetailSerializer,
    AvailabilitySerializer
)
from apps.accounts.permissions import IsProfessor, IsProfessorOrReadOnly
from apps.consultations.models import Consultation, ConsultationStatus


class ProfessorProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProfessorProfile model.
    """
    queryset = ProfessorProfile.objects.select_related('user').all()
    serializer_class = ProfessorProfileSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'department', 'title']
    ordering_fields = ['user__last_name', 'created_at']
    ordering = ['user__last_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve' or self.action == 'availability':
            return ProfessorProfileDetailSerializer
        return ProfessorProfileSerializer
    
    def get_permissions(self):
        """Return appropriate permissions."""
        if self.action in ['update', 'partial_update', 'availability']:
            return [IsAuthenticated(), IsProfessorOrReadOnly()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def availability(self, request, pk=None):
        """Get professor's available time slots."""
        professor = self.get_object()
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response(
                {'error': 'Date parameter is required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get day of week
        day_name = target_date.strftime('%A').lower()
        available_slots = professor.get_available_slots(day_name)
        
        # Get existing consultations for this date
        existing_consultations = Consultation.objects.filter(
            professor=professor.user,
            scheduled_date=target_date,
            status__in=[ConsultationStatus.PENDING, ConsultationStatus.CONFIRMED]
        ).values_list('scheduled_time', 'duration')
        
        # Calculate booked slots
        booked_slots = []
        buffer = professor.buffer_time_between_consultations
        
        for time, duration in existing_consultations:
            start = time
            end_time = (timezone.datetime.combine(target_date, start) + 
                       timedelta(minutes=duration + buffer)).time()
            booked_slots.append({'start': start.isoformat(), 'end': end_time.isoformat()})
        
        return Response({
            'professor_id': professor.id,
            'professor_name': professor.get_full_name(),
            'date': target_date.isoformat(),
            'available_slots': available_slots,
            'booked_slots': booked_slots,
            'consultation_duration_default': professor.consultation_duration_default,
            'buffer_time': professor.buffer_time_between_consultations
        })
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsProfessor])
    def update_availability(self, request, pk=None):
        """Update professor's availability."""
        professor = self.get_object()
        
        # Check if user owns this profile
        if professor.user != request.user:
            return Response(
                {'error': 'You can only update your own availability.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        professor.available_days = serializer.validated_data['available_days']
        professor.save()
        
        return Response({
            'message': 'Availability updated successfully.',
            'available_days': professor.available_days
        })

