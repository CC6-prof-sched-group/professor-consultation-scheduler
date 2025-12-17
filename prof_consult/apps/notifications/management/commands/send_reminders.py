from django.core.management.base import BaseCommand
from apps.notifications.tasks import send_24h_reminders

class Command(BaseCommand):
    help = 'Sends 24-hour reminders for upcoming consultations'

    def handle(self, *args, **options):
        self.stdout.write('Sending reminders...')
        try:
            send_24h_reminders()
            self.stdout.write(self.style.SUCCESS('Reminders sent successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send reminders: {str(e)}'))
