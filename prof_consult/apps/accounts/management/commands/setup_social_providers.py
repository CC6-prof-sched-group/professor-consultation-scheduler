import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
try:
    from decouple import config as dconfig
except Exception:
    def dconfig(key, default=None):
        return os.environ.get(key, default)

try:
    from allauth.socialaccount.models import SocialApp
except Exception:
    SocialApp = None


class Command(BaseCommand):
    help = 'Creates/updates SocialApp entries (e.g., Google) and links them to the current Site.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            default='google',
            help='OAuth provider to set up (default: google)'
        )
        parser.add_argument(
            '--name',
            default=None,
            help='Display name for the SocialApp (defaults based on provider)'
        )
        parser.add_argument(
            '--client-id',
            default=None,
            help='OAuth client ID (overrides env if provided)'
        )
        parser.add_argument(
            '--client-secret',
            default=None,
            help='OAuth client secret (overrides env if provided)'
        )
        parser.add_argument(
            '--delete-duplicates',
            action='store_true',
            help='Delete duplicate SocialApps for the provider after linking the current Site.'
        )

    def handle(self, *args, **options):
        if SocialApp is None:
            self.stdout.write(self.style.ERROR('django-allauth not installed or unavailable.'))
            return

        provider = options['provider']
        name = options['name'] or (provider.capitalize())

        # Resolve Site
        try:
            site = Site.objects.get(id=settings.SITE_ID)
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Site with ID {settings.SITE_ID} does not exist. Run migrations first.'
                )
            )
            return

        # Resolve credentials (prefer .env via decouple)
        env_map = {
            'google': {
                'id': ['GOOGLE_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_ID'],
                'secret': ['GOOGLE_CLIENT_SECRET', 'GOOGLE_OAUTH_CLIENT_SECRET'],
            }
        }

        def first_conf(keys):
            for k in keys:
                v = dconfig(k, default=None)
                if v:
                    return v
            return None

        client_id = options['client_id'] or first_conf(env_map.get(provider, {}).get('id', []))
        client_secret = options['client_secret'] or first_conf(env_map.get(provider, {}).get('secret', []))

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                'Missing OAuth credentials. Set env variables and re-run:\n'
                '  GOOGLE_CLIENT_ID / GOOGLE_OAUTH_CLIENT_ID\n'
                '  GOOGLE_CLIENT_SECRET / GOOGLE_OAUTH_CLIENT_SECRET\n'
                'Or pass --client-id and --client-secret.'
            ))
            return

        # Create or update SocialApp
        # Only use provider for lookup to avoid creating duplicates
        app, created = SocialApp.objects.get_or_create(
            provider=provider,
            defaults={'name': name}
        )
        # Update fields even if it already exists
        app.name = name
        app.client_id = client_id
        app.secret = client_secret
        # Optional key field (unused for Google)
        app.key = app.key or ''
        app.save()

        # Ensure Site link
        if site not in app.sites.all():
            app.sites.add(site)

        # Deduplicate: ensure only this app is linked to the current site
        duplicates = SocialApp.objects.filter(provider=provider).exclude(pk=app.pk)
        for dup in duplicates:
            if site in dup.sites.all():
                dup.sites.remove(site)
                self.stdout.write(self.style.WARNING(
                    f'Removed Site "{site.domain}" from duplicate SocialApp id={dup.id} name="{dup.name}"'
                ))
                if options.get('delete_duplicates'):
                    dup.delete()
                    self.stdout.write(self.style.WARNING(
                        f'Deleted duplicate SocialApp id={dup.id} name="{dup.name}"'
                    ))

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} SocialApp for provider "{provider}" and linked to Site "{site.domain}"'
            )
        )
