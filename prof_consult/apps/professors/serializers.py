"""
Serializers for professors app.
"""
from rest_framework import serializers
from apps.professors.models import ProfessorProfile
from apps.accounts.serializers import UserSerializer


class ProfessorProfileSerializer(serializers.ModelSerializer):
    """Serializer for ProfessorProfile model."""
    
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfessorProfile
        fields = [
            'id', 'user', 'title', 'department', 'office_location',
            'consultation_duration_default', 'available_days',
            'max_advance_booking_days', 'buffer_time_between_consultations',
            'created_at', 'updated_at', 'full_name', 'email'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get professor's full name."""
        return obj.get_full_name()
    
    def get_email(self, obj):
        """Get professor's email."""
        return obj.user.email


class ProfessorProfileDetailSerializer(ProfessorProfileSerializer):
    """Detailed serializer for ProfessorProfile."""
    
    class Meta(ProfessorProfileSerializer.Meta):
        fields = ProfessorProfileSerializer.Meta.fields


class AvailabilitySerializer(serializers.Serializer):
    """Serializer for updating availability."""
    
    available_days = serializers.DictField(
        help_text="Dictionary with day names as keys and time slots as values"
    )
    
    def validate_available_days(self, value):
        """Validate available_days structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("available_days must be a dictionary.")
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in value.keys():
            if day.lower() not in valid_days:
                raise serializers.ValidationError(f"Invalid day: {day}. Must be one of {valid_days}.")
        return value

