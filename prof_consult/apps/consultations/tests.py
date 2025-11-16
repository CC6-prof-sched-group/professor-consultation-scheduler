"""
Tests for consultations app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, time, timedelta
from django.utils import timezone

from apps.consultations.models import Consultation, ConsultationStatus
from apps.professors.models import ProfessorProfile

User = get_user_model()


class ConsultationModelTest(TestCase):
    """Test Consultation model."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='testpass123',
            role='STUDENT'
        )
        self.professor = User.objects.create_user(
            email='professor@example.com',
            username='professor',
            password='testpass123',
            role='PROFESSOR'
        )
        self.professor_profile = ProfessorProfile.objects.create(
            user=self.professor,
            title='Dr.',
            department='Computer Science'
        )
        self.consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            duration=30
        )
    
    def test_consultation_creation(self):
        """Test consultation creation."""
        self.assertEqual(self.consultation.status, ConsultationStatus.PENDING)
        self.assertEqual(self.consultation.student, self.student)
        self.assertEqual(self.consultation.professor, self.professor)
    
    def test_confirm_consultation(self):
        """Test confirming a consultation."""
        result = self.consultation.confirm()
        self.assertTrue(result)
        self.assertEqual(self.consultation.status, ConsultationStatus.CONFIRMED)
        self.assertIsNotNone(self.consultation.confirmed_at)
    
    def test_cancel_consultation(self):
        """Test cancelling a consultation."""
        self.consultation.confirm()
        result = self.consultation.cancel(reason='Test cancellation')
        self.assertTrue(result)
        self.assertEqual(self.consultation.status, ConsultationStatus.CANCELLED)
        self.assertIsNotNone(self.consultation.cancelled_at)


class ConsultationAPITest(APITestCase):
    """Test Consultation API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='testpass123',
            role='STUDENT'
        )
        self.professor = User.objects.create_user(
            email='professor@example.com',
            username='professor',
            password='testpass123',
            role='PROFESSOR'
        )
        self.professor_profile = ProfessorProfile.objects.create(
            user=self.professor,
            title='Dr.',
            department='Computer Science'
        )
        self.consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            duration=30
        )
    
    def test_create_consultation(self):
        """Test creating a consultation."""
        self.client.force_authenticate(user=self.student)
        data = {
            'professor_id': self.professor.id,
            'title': 'New Consultation',
            'description': 'Test description',
            'scheduled_date': str(date.today() + timedelta(days=2)),
            'scheduled_time': '15:00:00',
            'duration': 30
        }
        response = self.client.post('/api/consultations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_confirm_consultation(self):
        """Test confirming a consultation."""
        self.client.force_authenticate(user=self.professor)
        response = self.client.patch(f'/api/consultations/{self.consultation.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.status, ConsultationStatus.CONFIRMED)

