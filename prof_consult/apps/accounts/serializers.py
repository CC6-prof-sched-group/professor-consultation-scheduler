"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.professors.models import ProfessorProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'profile_picture', 'department', 'bio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        """Ensure email is unique."""
        if self.instance and self.instance.email == value:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserDetailSerializer(UserSerializer):
    """Detailed serializer for User with additional fields."""
    
    has_professor_profile = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['has_professor_profile']
    
    def get_has_professor_profile(self, obj):
        """Check if user has a professor profile."""
        return hasattr(obj, 'professor_profile')


class ProfessorProfileSerializer(serializers.ModelSerializer):
    """Serializer for ProfessorProfile model."""
    
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfessorProfile
        fields = [
            'id', 'user', 'title', 'department', 'office_location',
            'consultation_duration_default', 'available_days',
            'max_advance_booking_days', 'buffer_time_between_consultations',
            'created_at', 'updated_at', 'full_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get professor's full name."""
        return obj.get_full_name()
    
    def validate_available_days(self, value):
        """Validate available_days JSON structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("available_days must be a dictionary.")
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in value.keys():
            if day.lower() not in valid_days:
                raise serializers.ValidationError(f"Invalid day: {day}. Must be one of {valid_days}.")
        return value

