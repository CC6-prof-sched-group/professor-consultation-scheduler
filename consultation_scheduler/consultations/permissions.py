from rest_framework import permissions

class IsProfessor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'professor'

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'student'