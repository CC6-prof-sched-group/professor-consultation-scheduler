"""
Views for consultations app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

from apps.consultations.models import Consultation, ConsultationStatus
from apps.consultations.serializers import (
    ConsultationSerializer, ConsultationCreateSerializer,
    ConsultationUpdateSerializer, ConsultationActionSerializer,
    ConsultationRateSerializer, ConsultationNotesSerializer
)
from apps.accounts.permissions import (
    IsStudent, IsProfessor, IsAdmin, IsOwnerOrProfessor
)
from apps.integrations.services import GoogleCalendarService
from apps.notifications.tasks import (
    send_booking_created_notification,
    send_booking_confirmed_notification,
    send_booking_cancelled_notification,
    send_booking_rescheduled_notification
)

@login_required
@require_http_methods(["POST"])
def check_availability(request):
    """Check if a professor is available at a specific date/time."""
    professor_id = request.POST.get('professor_id')
    date = request.POST.get('date')
    time = request.POST.get('time')
    duration = int(request.POST.get('duration', 30))
    consultation_id = request.POST.get('consultation_id')  # For rescheduling
    
    if not all([professor_id, date, time]):
        return JsonResponse({'available': False, 'message': 'Missing required fields'})
    
    try:
        professor = User.objects.get(id=professor_id, role='PROFESSOR')
        
        # Parse the date and time
        requested_datetime = timezone.make_aware(
            datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        )
        requested_end = requested_datetime + timedelta(minutes=duration)
        
        # Check if it's in the past
        if requested_datetime < timezone.now():
            return JsonResponse({
                'available': False,
                'message': 'Cannot book consultations in the past'
            })
        
        # Check professor's availability schedule
        weekday = requested_datetime.strftime('%A').upper()
        availability = professor.availability.filter(
            day_of_week=weekday,
            is_available=True
        ).first()
        
        if not availability:
            return JsonResponse({
                'available': False,
                'message': f'Professor is not available on {weekday}s'
            })
        
        # Check if time falls within availability hours
        requested_time = requested_datetime.time()
        if not (availability.start_time <= requested_time <= availability.end_time):
            return JsonResponse({
                'available': False,
                'message': f'Professor is only available from {availability.start_time.strftime("%I:%M %p")} to {availability.end_time.strftime("%I:%M %p")} on {weekday}s'
            })
        
        # Check for conflicting consultations
        conflicting = Consultation.objects.filter(
            professor=professor,
            scheduled_date=requested_datetime.date(),
            status__in=['PENDING', 'CONFIRMED']
        ).exclude(id=consultation_id) if consultation_id else Consultation.objects.filter(
            professor=professor,
            scheduled_date=requested_datetime.date(),
            status__in=['PENDING', 'CONFIRMED']
        )
        
        for consultation in conflicting:
            existing_start = timezone.make_aware(
                datetime.combine(consultation.scheduled_date, consultation.scheduled_time)
            )
            existing_end = existing_start + timedelta(minutes=consultation.duration)
            
            # Check for overlap
            if (requested_datetime < existing_end and requested_end > existing_start):
                return JsonResponse({
                    'available': False,
                    'message': f'Time slot conflicts with existing consultation at {consultation.scheduled_time.strftime("%I:%M %p")}'
                })
        
        return JsonResponse({
            'available': True,
            'message': 'Time slot is available'
        })
        
    except User.DoesNotExist:
        return JsonResponse({'available': False, 'message': 'Professor not found'})
    except Exception as e:
        return JsonResponse({'available': False, 'message': str(e)})

class ConsultationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Consultation model.
    """
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'professor', 'student']
    search_fields = ['title', 'description']
    ordering_fields = ['scheduled_date', 'scheduled_time', 'created_at']
    ordering = ['-scheduled_date', '-scheduled_time']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return ConsultationCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ConsultationUpdateSerializer
        return ConsultationSerializer
    
    def get_queryset(self):
        """Filter consultations based on user role."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Filter by role
        if user.is_student():
            queryset = queryset.filter(student=user)
        elif user.is_professor():
            queryset = queryset.filter(professor=user)
        elif not user.is_admin():
            queryset = queryset.none()
        
        # Additional filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        
        return queryset.select_related('student', 'professor')
    
    def get_permissions(self):
        """Return appropriate permissions."""
        if self.action == 'create':
            return [IsAuthenticated(), IsStudent()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrProfessor()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create consultation and send notifications."""
        consultation = serializer.save(
            student=self.request.user,
            status=ConsultationStatus.PENDING
        )
        
        # Send notifications asynchronously
        send_booking_created_notification.delay(consultation.id)
        
        return consultation
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsProfessor])
    def confirm(self, request, pk=None):
        """Confirm a consultation."""
        consultation = self.get_object()
        
        if consultation.status != ConsultationStatus.PENDING:
            return Response(
                {'error': 'Only pending consultations can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Confirm consultation
        consultation.confirm()
        
        # Create Google Calendar event
        calendar_service = GoogleCalendarService(consultation.professor)
        event_id = calendar_service.create_event(consultation)
        if event_id:
            consultation.google_calendar_event_id = event_id
            consultation.save()
        
        # Send confirmation notification
        send_booking_confirmed_notification.delay(consultation.id)
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOwnerOrProfessor])
    def cancel(self, request, pk=None):
        """Cancel a consultation."""
        consultation = self.get_object()
        serializer = ConsultationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not consultation.can_be_cancelled():
            return Response(
                {'error': 'This consultation cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = serializer.validated_data.get('reason', '')
        
        # Delete Google Calendar event if exists
        if consultation.google_calendar_event_id:
            calendar_service = GoogleCalendarService(consultation.professor)
            calendar_service.delete_event(consultation.google_calendar_event_id)
        
        # Cancel consultation
        consultation.cancel(reason=reason)
        
        # Send cancellation notification
        send_booking_cancelled_notification.delay(consultation.id, reason)
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOwnerOrProfessor])
    def reschedule(self, request, pk=None):
        """Reschedule a consultation."""
        consultation = self.get_object()
        
        if consultation.status != ConsultationStatus.CONFIRMED:
            return Response(
                {'error': 'Only confirmed consultations can be rescheduled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update consultation
        update_serializer = ConsultationUpdateSerializer(
            consultation,
            data=request.data,
            partial=True
        )
        update_serializer.is_valid(raise_exception=True)
        update_serializer.save(status=ConsultationStatus.PENDING)
        
        # Update Google Calendar event if exists
        if consultation.google_calendar_event_id:
            calendar_service = GoogleCalendarService(consultation.professor)
            calendar_service.update_event(consultation)
        
        # Send reschedule notification
        send_booking_rescheduled_notification.delay(consultation.id)
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsProfessor])
    def complete(self, request, pk=None):
        """Mark consultation as completed."""
        consultation = self.get_object()
        
        if consultation.status != ConsultationStatus.CONFIRMED:
            return Response(
                {'error': 'Only confirmed consultations can be completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.complete()
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsProfessor])
    def no_show(self, request, pk=None):
        """Mark consultation as no-show."""
        consultation = self.get_object()
        
        if consultation.status != ConsultationStatus.CONFIRMED:
            return Response(
                {'error': 'Only confirmed consultations can be marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.mark_no_show()
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsProfessor])
    def notes(self, request, pk=None):
        """Add notes to consultation."""
        consultation = self.get_object()
        serializer = ConsultationNotesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        consultation.notes = serializer.validated_data['notes']
        consultation.save()
        
        response_serializer = self.get_serializer(consultation)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStudent])
    def rate(self, request, pk=None):
        """Rate a completed consultation."""
        consultation = self.get_object()
        
        if consultation.student != request.user:
            return Response(
                {'error': 'You can only rate your own consultations.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not consultation.can_be_rated():
            return Response(
                {'error': 'This consultation cannot be rated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ConsultationRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        consultation.rating = serializer.validated_data['rating']
        consultation.feedback = serializer.validated_data.get('feedback', '')
        consultation.save()
        
        response_serializer = self.get_serializer(consultation)
        return Response(response_serializer.data)