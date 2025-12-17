from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Configures Django Sites for Local and Production environments'

    def handle(self, *args, **options):
        self.stdout.write('Configuring Sites...')

        # 1. Configure Localhost (ID=1)
        site_local, created = Site.objects.update_or_create(
            pk=1,
            defaults={
                'domain': '127.0.0.1:8000',
                'name': 'Localhost'
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Site 1: {site_local.domain}"))

        # 2. Configure Production (ID=2)
        # We assume the production domain is consultease.pythonanywhere.com based on user reports
        prod_domain = 'consultease.pythonanywhere.com'
        site_prod, created = Site.objects.update_or_create(
            pk=2,
            defaults={
                'domain': prod_domain,
                'name': 'ConsultEase Production'
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Site 2: {site_prod.domain}"))
        
        self.stdout.write(self.style.SUCCESS('Sites configured successfully.'))
