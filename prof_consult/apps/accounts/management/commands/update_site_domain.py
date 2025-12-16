from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Updates the Site domain from environment configuration'

    def handle(self, *args, **options):
        site_domain = settings.SITE_DOMAIN
        
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            old_domain = site.domain
            
            if site.domain != site_domain:
                site.domain = site_domain
                site.name = site_domain
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated Site domain from "{old_domain}" to "{site_domain}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Site domain already set to "{site_domain}"')
                )
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Site with ID {settings.SITE_ID} does not exist. Run migrations first.'
                )
            )
