from rest_framework import serializers
from .models import ConsultationSlot, Booking, ConsultationNote
from accounts.serializers import UserSerializer

class ConsultationSlotSerializer(serializers.ModelSerializer):
    professor = UserSerializer(read_only=True)
    available_spots = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultationSlot
        fields = ['id', 'professor', 'title', 'description', 'start_time', 
                  'end_time', 'status', 'max_students', 'location', 
                  'is_online', 'meeting_link', 'available_spots', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'professor', 'status', 'created_at', 'updated_at']
    
    def get_available_spots(self, obj):
        booked = obj.bookings.filter(status__in=['pending', 'confirmed']).count()
        return obj.max_students - booked
    
    def validate(self, data):
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        return data
    
class BookingSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    slot = ConsultationSlotSerializer(read_only=True)
    slot_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'slot', 'slot_id', 'student', 'status', 'reason', 
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'student', 'status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        slot_id = validated_data.pop('slot_id')
        slot = ConsultationSlot.objects.get(id=slot_id)
        
        # Check if slot is available
        if slot.status != 'available':
            raise serializers.ValidationError("This slot is not available")
        
        # Check if student already booked this slot
        if Booking.objects.filter(
            slot=slot,
            student=self.context['request'].user,
            status__in=['pending', 'confirmed']
        ).exists():
            raise serializers.ValidationError("You have already booked this slot")
        
        # Check if slot is full
        booked_count = slot.bookings.filter(status__in=['pending', 'confirmed']).count()
        if booked_count >= slot.max_students:
            raise serializers.ValidationError("This slot is fully booked")
        
        validated_data['slot'] = slot
        validated_data['student'] = self.context['request'].user
        
        return super().create(validated_data)
    
class ConsultationNoteSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)
    
    class Meta:
        model = ConsultationNote
        fields = ['id', 'booking', 'professor_notes', 'student_feedback', 
                  'rating', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']