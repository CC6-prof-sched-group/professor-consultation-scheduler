from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Accounts'
    
    def ready(self):
        # Import signal handlers to ensure they're registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass

