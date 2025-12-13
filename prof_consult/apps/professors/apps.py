from django.apps import AppConfig


class ProfessorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.professors'
    verbose_name = 'Professors'
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.professors.signals  