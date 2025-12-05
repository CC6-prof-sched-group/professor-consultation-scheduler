"""
Serializers for consultations app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.consultations.models import Consultation, ConsultationStatus
from apps.accounts.serializers import UserSerializer

User = get_user_model()


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer for Consultation model."""
    
    student = UserSerializer(read_only=True)
    professor = UserSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STUDENT'),
        source='student',
        write_only=True,
        required=False
    )
    professor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='PROFESSOR'),
        source='professor',
        write_only=True
    )
    datetime = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    can_be_rated = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    can_be_rescheduled = serializers.SerializerMethodField()
    cancellation_deadline = serializers.SerializerMethodField()
    hours_until_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'student', 'professor', 'student_id', 'professor_id',
            'title', 'description', 'scheduled_date', 'scheduled_time',
            'duration', 'status', 'booking_created_at', 'confirmed_at',
            'cancelled_at', 'cancellation_reason', 'google_calendar_event_id',
            'meeting_link', 'location', 'notes', 'rating', 'feedback',
            'created_at', 'updated_at', 'datetime', 'is_past',
            'can_be_rated', 'can_be_cancelled', 'can_be_rescheduled',
            'cancellation_deadline', 'hours_until_deadline'
        ]
        read_only_fields = [
            'id', 'status', 'booking_created_at', 'confirmed_at',
            'cancelled_at', 'google_calendar_event_id', 'created_at',
            'updated_at'
        ]
    
    def get_datetime(self, obj):
        """Get combined scheduled date and time."""
        return obj.get_datetime().isoformat() if obj.scheduled_date and obj.scheduled_time else None
    
    def get_is_past(self, obj):
        """Check if consultation is in the past."""
        return obj.is_past()
    
    def get_can_be_rated(self, obj):
        """Check if consultation can be rated."""
        return obj.can_be_rated()
    
    def get_can_be_cancelled(self, obj):
        """Check if consultation can be cancelled."""
        return obj.can_be_cancelled()
    
    def get_can_be_rescheduled(self, obj):
        """Check if consultation can be rescheduled."""
        return obj.can_be_rescheduled()
    
    def get_cancellation_deadline(self, obj):
        """Get cancellation deadline datetime."""
        deadline = obj.get_cancellation_deadline()
        return deadline.isoformat() if deadline else None
    
    def get_hours_until_deadline(self, obj):
        """Get hours remaining until cancellation deadline."""
        return obj.get_hours_until_deadline()
    
    def validate(self, data):
        """Validate consultation data."""
        # Set student to current user if not provided
        if not data.get('student') and 'request' in self.context:
            data['student'] = self.context['request'].user
        
        # Check if professor has availability
        professor = data.get('professor')
        if professor and hasattr(professor, 'professor_profile'):
            profile = professor.professor_profile
            
            # Check max advance booking days
            from django.utils import timezone
            scheduled_date = data.get('scheduled_date')
            if scheduled_date:
                days_ahead = (scheduled_date - timezone.now().date()).days
                if days_ahead > profile.max_advance_booking_days:
                    raise serializers.ValidationError(
                        f"Cannot book more than {profile.max_advance_booking_days} days in advance."
                    )
        
        return data


class ConsultationCreateSerializer(ConsultationSerializer):
    """Serializer for creating consultations."""
    
    class Meta(ConsultationSerializer.Meta):
        pass


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating consultations."""
    
    class Meta:
        model = Consultation
        fields = ['title', 'description', 'scheduled_date', 'scheduled_time', 'duration', 'location']


class ConsultationActionSerializer(serializers.Serializer):
    """Serializer for consultation actions."""
    
    reason = serializers.CharField(required=False, allow_blank=True, help_text="Reason for cancellation")


class ConsultationRateSerializer(serializers.Serializer):
    """Serializer for rating consultations."""
    
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True)


class ConsultationNotesSerializer(serializers.Serializer):
    """Serializer for adding notes to consultations."""
    
    notes = serializers.CharField(help_text="Professor notes after consultation")



class CancellationRecordSerializer(serializers.ModelSerializer):
    """Serializer for CancellationRecord model."""
    consultation = ConsultationSerializer(read_only=True)
    consultation_id = serializers.PrimaryKeyRelatedField(
        queryset=Consultation.objects.all(),
        source='consultation',
        write_only=True
    )
    requested_by = UserSerializer(read_only=True)

    class Meta:
        model = __import__('apps.consultations.models', fromlist=['CancellationRecord']).CancellationRecord
        fields = ['id', 'consultation', 'consultation_id', 'requested_by', 'requested_at', 'reason', 'status', 'processed_by', 'processed_at', 'admin_note']
        read_only_fields = ['id', 'requested_at', 'status', 'processed_by', 'processed_at']


class RescheduleRequestSerializer(serializers.ModelSerializer):
    """Serializer for RescheduleRequest model."""
    consultation = ConsultationSerializer(read_only=True)
    consultation_id = serializers.PrimaryKeyRelatedField(
        queryset=Consultation.objects.all(),
        source='consultation',
        write_only=True
    )
    requested_by = UserSerializer(read_only=True)

    class Meta:
        model = __import__('apps.consultations.models', fromlist=['RescheduleRequest']).RescheduleRequest
        fields = ['id', 'consultation', 'consultation_id', 'requested_by', 'requested_at', 'new_date', 'new_time', 'new_duration', 'reason', 'status', 'processed_by', 'processed_at', 'admin_note']
        read_only_fields = ['id', 'requested_at', 'status', 'processed_by', 'processed_at']

