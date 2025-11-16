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
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'student', 'professor', 'student_id', 'professor_id',
            'title', 'description', 'scheduled_date', 'scheduled_time',
            'duration', 'status', 'booking_created_at', 'confirmed_at',
            'cancelled_at', 'cancellation_reason', 'google_calendar_event_id',
            'meeting_link', 'location', 'notes', 'rating', 'feedback',
            'created_at', 'updated_at', 'datetime', 'is_past',
            'can_be_rated', 'can_be_cancelled'
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

