from django.core.management.base import BaseCommand
from apps.integrations.tasks import sync_google_calendar_events

class Command(BaseCommand):
    help = 'Syncs consultation status with Google Calendar events'

    def handle(self, *args, **options):
        self.stdout.write('Starting calendar sync...')
        try:
            sync_google_calendar_events()
            self.stdout.write(self.style.SUCCESS('Calendar sync completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Calendar sync failed: {str(e)}'))
