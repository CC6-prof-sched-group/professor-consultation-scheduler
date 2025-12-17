import os
import socket
from django.conf import settings
from django.contrib.sites.models import Site

def diagnose():
    print("--- Diagnostic Report ---")
    print(f"Hostname: {socket.gethostname()}")
    print(f"SITE_ID from settings: {settings.SITE_ID}")
    
    try:
        current_site = Site.objects.get(pk=settings.SITE_ID)
        print(f"Current Site (ID={settings.SITE_ID}):")
        print(f"  Domain: {current_site.domain}")
        print(f"  Name: {current_site.name}")
    except Site.DoesNotExist:
        print(f"ERROR: Site with ID {settings.SITE_ID} does not exist!")
    
    print(f"SECURE_PROXY_SSL_HEADER: {getattr(settings, 'SECURE_PROXY_SSL_HEADER', 'Not Set')}")
    print(f"ACCOUNT_DEFAULT_HTTP_PROTOCOL: {getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'Not Set')}")
    print(f"SOCIALACCOUNT_PROVIDERS (Google): {settings.SOCIALACCOUNT_PROVIDERS.get('google', {})}")
    
    print("\n--- All Sites ---")
    for s in Site.objects.all():
        print(f"ID: {s.id} | Domain: {s.domain} | Name: {s.name}")

if __name__ == "__main__":
    import django
    django.setup()
    diagnose()
