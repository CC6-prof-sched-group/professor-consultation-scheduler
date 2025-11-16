"""
Admin configuration for professors app.
"""
from django.contrib import admin
from apps.professors.models import ProfessorProfile


@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    """Admin interface for ProfessorProfile model."""
    list_display = ['user', 'title', 'department', 'office_location', 'consultation_duration_default', 'created_at']
    list_filter = ['department', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'department', 'title']
    readonly_fields = ['created_at', 'updated_at']

