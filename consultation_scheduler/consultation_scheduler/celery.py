import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consultation_scheduler.settings')

app = Celery('consultation_scheduler')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'send-reminders-every-hour': {
        'task': 'notifications.scheduler.schedule_reminders',
        'schedule': crontab(minute=0),  # Run every hour
    },
}