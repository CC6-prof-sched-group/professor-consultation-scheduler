from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

try:
    from allauth.socialaccount.models import SocialApp
except Exception:
    SocialApp = None


class Command(BaseCommand):
    help = 'Removes duplicate SocialApp entries for each provider, keeping only one per provider'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--provider',
            default=None,
            help='Only clean up a specific provider (e.g., google)'
        )

    def handle(self, *args, **options):
        if SocialApp is None:
            self.stdout.write(self.style.ERROR('django-allauth not installed or unavailable.'))
            return

        dry_run = options['dry_run']
        provider_filter = options['provider']

        # Get current site
        try:
            site = Site.objects.get(id=settings.SITE_ID)
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Site with ID {settings.SITE_ID} does not exist.'
                )
            )
            return

        # Get all providers
        if provider_filter:
            providers = [provider_filter]
        else:
            providers = SocialApp.objects.values_list('provider', flat=True).distinct()

        total_deleted = 0

        for provider in providers:
            apps = SocialApp.objects.filter(provider=provider).order_by('id')
            count = apps.count()

            if count <= 1:
                self.stdout.write(f'Provider "{provider}": {count} app(s) found, no duplicates.')
                continue

            # Keep the first one, delete the rest
            apps_list = list(apps)
            keep_app = apps_list[0]
            duplicates = apps_list[1:]

            self.stdout.write(
                self.style.WARNING(
                    f'Provider "{provider}": Found {count} apps, keeping ID={keep_app.id} "{keep_app.name}"'
                )
            )

            # Ensure the kept app is linked to the current site
            if site not in keep_app.sites.all():
                if not dry_run:
                    keep_app.sites.add(site)
                self.stdout.write(f'  → Linked ID={keep_app.id} to site "{site.domain}"')

            # Delete duplicates
            for dup in duplicates:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  → [DRY RUN] Would delete ID={dup.id} "{dup.name}"'
                        )
                    )
                else:
                    dup_id = dup.id
                    dup_name = dup.name
                    dup.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  → Deleted ID={dup_id} "{dup_name}"'
                        )
                    )
                total_deleted += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would have deleted {total_deleted} duplicate SocialApp(s).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDeleted {total_deleted} duplicate SocialApp(s).'
                )
            )
