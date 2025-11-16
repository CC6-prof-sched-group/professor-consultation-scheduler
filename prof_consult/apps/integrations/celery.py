"""
Celery app for integrations (re-export from main celery app).
"""
from prof_consult.celery import app

__all__ = ['app']

