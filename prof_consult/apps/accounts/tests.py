"""
Tests for accounts app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user creation."""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'STUDENT')
        self.assertTrue(self.user.is_student())
    
    def test_user_roles(self):
        """Test user role methods."""
        self.user.role = 'PROFESSOR'
        self.assertTrue(self.user.is_professor())
        
        self.user.role = 'ADMIN'
        self.assertTrue(self.user.is_admin())


class UserAPITest(APITestCase):
    """Test User API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_get_current_user(self):
        """Test getting current user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

