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


class ConsultationCancellationPolicyTest(TestCase):
    """Test cancellation and reschedule time limit policy."""
    
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
        # Create professor profile with 4-hour cancellation notice
        self.professor_profile = ProfessorProfile.objects.create(
            user=self.professor,
            title='Dr.',
            department='Computer Science',
            cancellation_notice_hours=4
        )
    
    def test_can_cancel_outside_notice_period(self):
        """Test that consultation can be cancelled outside the notice period."""
        # Create consultation 24 hours from now
        future_time = timezone.now() + timedelta(hours=24)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Should be able to cancel (24 hours > 4 hours notice required)
        self.assertTrue(consultation.can_be_cancelled())
    
    def test_cannot_cancel_within_notice_period(self):
        """Test that consultation cannot be cancelled within the notice period."""
        # Create consultation 2 hours from now (less than 4-hour notice)
        future_time = timezone.now() + timedelta(hours=2)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Should NOT be able to cancel (2 hours < 4 hours notice required)
        self.assertFalse(consultation.can_be_cancelled())
    
    def test_can_reschedule_outside_notice_period(self):
        """Test that consultation can be rescheduled outside the notice period."""
        # Create consultation 24 hours from now
        future_time = timezone.now() + timedelta(hours=24)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Should be able to reschedule (24 hours > 4 hours notice required)
        self.assertTrue(consultation.can_be_rescheduled())
    
    def test_cannot_reschedule_within_notice_period(self):
        """Test that consultation cannot be rescheduled within the notice period."""
        # Create consultation 2 hours from now (less than 4-hour notice)
        future_time = timezone.now() + timedelta(hours=2)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Should NOT be able to reschedule (2 hours < 4 hours notice required)
        self.assertFalse(consultation.can_be_rescheduled())
    
    def test_cancellation_deadline_calculation(self):
        """Test that cancellation deadline is correctly calculated."""
        # Create consultation 24 hours from now
        future_time = timezone.now() + timedelta(hours=24)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=self.professor,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        deadline = consultation.get_cancellation_deadline()
        # Deadline should be 4 hours before the scheduled time
        expected_deadline = consultation.get_scheduled_datetime() - timedelta(hours=4)
        
        # Allow 1-second tolerance for execution time
        time_diff = abs((deadline - expected_deadline).total_seconds())
        self.assertLess(time_diff, 1)
    
    def test_zero_cancellation_notice_hours(self):
        """Test when professor has 0 cancellation notice hours."""
        # Create professor with no cancellation notice requirement
        prof_no_notice = User.objects.create_user(
            email='professor2@example.com',
            username='professor2',
            password='testpass123',
            role='PROFESSOR'
        )
        prof_profile_no_notice = ProfessorProfile.objects.create(
            user=prof_no_notice,
            title='Dr.',
            department='Computer Science',
            cancellation_notice_hours=0  # No notice required
        )
        
        # Create consultation 1 minute from now
        future_time = timezone.now() + timedelta(minutes=1)
        consultation = Consultation.objects.create(
            student=self.student,
            professor=prof_no_notice,
            title='Test Consultation',
            description='Test description',
            scheduled_date=future_time.date(),
            scheduled_time=future_time.time(),
            duration=30,
            status=ConsultationStatus.CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Should be able to cancel anytime
        self.assertTrue(consultation.can_be_cancelled())


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
            department='Computer Science',
            cancellation_notice_hours=4
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

