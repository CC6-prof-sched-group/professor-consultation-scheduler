"""
Tests for professors app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.professors.models import ProfessorProfile

User = get_user_model()


class ProfessorProfileModelTest(TestCase):
    """Test ProfessorProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='professor@example.com',
            username='professor',
            password='testpass123',
            role='PROFESSOR'
        )
        self.profile = ProfessorProfile.objects.create(
            user=self.user,
            title='Dr.',
            department='Computer Science',
            office_location='Room 101',
            consultation_duration_default=30
        )
    
    def test_profile_creation(self):
        """Test profile creation."""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.title, 'Dr.')
        self.assertEqual(self.profile.department, 'Computer Science')
    
    def test_get_available_slots(self):
        """Test getting available slots."""
        self.profile.available_days = {
            'monday': ['09:00', '10:00', '11:00']
        }
        self.profile.save()
        slots = self.profile.get_available_slots('monday')
        self.assertEqual(len(slots), 3)
    
    def test_set_available_slots(self):
        """Test setting available slots."""
        slots = ['09:00', '10:00', '11:00']
        self.profile.set_available_slots('monday', slots)
        self.assertEqual(self.profile.get_available_slots('monday'), slots)

