"""
User models for the consultation scheduling system.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os


class Role(models.TextChoices):
    """User role choices."""
    STUDENT = 'STUDENT', 'Student'
    PROFESSOR = 'PROFESSOR', 'Professor'
    ADMIN = 'ADMIN', 'Admin'


class EncryptedField:
    """Helper class for encrypting/decrypting sensitive data."""
    
    @staticmethod
    def get_key():
        """Get encryption key from settings or generate one."""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # For development only - in production, set this in settings
            key = Fernet.generate_key()
        if isinstance(key, str):
            key = key.encode()
        return key
    
    @staticmethod
    def encrypt(value):
        """Encrypt a string value."""
        if not value:
            return None
        key = EncryptedField.get_key()
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt(encrypted_value):
        """Decrypt an encrypted string value."""
        if not encrypted_value:
            return None
        try:
            key = EncryptedField.get_key()
            f = Fernet(key)
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return None


class EncryptedTextField(models.TextField):
    """Text field that encrypts data before saving."""
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None:
            return value
        return EncryptedField.decrypt(value)
    
    def to_python(self, value):
        """Return value as-is for Python objects."""
        if isinstance(value, str):
            return value
        if value is None:
            return value
        return EncryptedField.decrypt(value)
    
    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None:
            return value
        return EncryptedField.encrypt(value)


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    
    Attributes:
        email: User's email address (unique, required)
        role: User role (STUDENT, PROFESSOR, ADMIN)
        google_id: Google OAuth2 ID
        google_access_token: Encrypted Google access token
        google_refresh_token: Encrypted Google refresh token
        profile_picture: URL or path to profile picture
        department: User's department
        bio: User biography
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="User's email address (unique, required)"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="User role in the system"
    )
    google_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Google OAuth2 user ID"
    )
    google_access_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text="Encrypted Google OAuth2 access token"
    )
    google_refresh_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text="Encrypted Google OAuth2 refresh token"
    )
    profile_picture = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to user's profile picture"
    )
    department = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="User's department"
    )
    student_id = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="Student ID (required for students)"
    )
    bio = models.TextField(
        null=True,
        blank=True,
        help_text="User biography"
    )
    profile_setup_completed = models.BooleanField(
        default=False,
        help_text="Whether user has completed initial profile setup (role selection)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['google_id']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
    def is_student(self):
        """Check if user is a student."""
        return self.role == Role.STUDENT
    
    def is_professor(self):
        """Check if user is a professor."""
        return self.role == Role.PROFESSOR
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == Role.ADMIN
    
    def get_google_access_token(self):
        """Get decrypted Google access token."""
        return EncryptedField.decrypt(self.google_access_token)
    
    def get_google_refresh_token(self):
        """Get decrypted Google refresh token."""
        return EncryptedField.decrypt(self.google_refresh_token)

