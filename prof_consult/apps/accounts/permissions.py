"""
Custom permissions for the consultation scheduling system.
"""
from rest_framework import permissions


class IsStudent(permissions.BasePermission):
    """Permission to allow only students to perform actions."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_student()
        )


class IsProfessor(permissions.BasePermission):
    """Permission to allow only professors to perform actions."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_professor()
        )


class IsAdmin(permissions.BasePermission):
    """Permission to allow only admins to perform actions."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin()
        )


class IsOwnerOrProfessor(permissions.BasePermission):
    """Permission to allow owner or professor to access object."""
    
    def has_object_permission(self, request, view, obj):
        # For consultations
        if hasattr(obj, 'student') and hasattr(obj, 'professor'):
            return obj.student == request.user or obj.professor == request.user
        # For other objects with user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to allow owner to edit, others to read only."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'student'):
            return obj.student == request.user
        return False


class IsProfessorOrReadOnly(permissions.BasePermission):
    """Permission to allow professors to edit, others to read only."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_professor()

