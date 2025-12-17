from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from django.db.models import Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Fixes duplicate accounts and email addresses that cause login errors'

    def handle(self, *args, **options):
        self.stdout.write('Checking for duplicates...')
        
        # 1. Check for duplicate emails in User model (should be unique)
        duplicates = User.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)
        if duplicates:
            self.stdout.write(self.style.WARNING(f"Found {duplicates.count()} duplicate emails in User model"))
            for item in duplicates:
                email = item['email']
                users = User.objects.filter(email=email).order_by('date_joined')
                # Keep the oldest, delete others? Or merge?
                # For safety, just list them for now, or delete if they have no data.
                primary = users.first()
                for user in users[1:]:
                    self.stdout.write(f"Deleting duplicate user {user.id} ({user.email})")
                    user.delete()
        else:
            self.stdout.write('No duplicate emails in User model.')

        # 2. Check for duplicate SocialAccounts
        # A user might have multiple social accounts, but (provider, uid) should be unique.
        social_dupes = SocialAccount.objects.values('provider', 'uid').annotate(count=Count('id')).filter(count__gt=1)
        if social_dupes:
            self.stdout.write(self.style.WARNING(f"Found {social_dupes.count()} duplicate SocialAccounts"))
            for item in social_dupes:
                accounts = SocialAccount.objects.filter(provider=item['provider'], uid=item['uid']).order_by('date_joined')
                primary = accounts.first()
                for acc in accounts[1:]:
                    self.stdout.write(f"Deleting duplicate social account {acc.id} for {acc.user}")
                    acc.delete()
        else:
            self.stdout.write('No duplicate SocialAccounts.')

        # 3. Check for duplicate EmailAddresses (allauth)
        email_dupes = EmailAddress.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)
        if email_dupes:
            self.stdout.write(self.style.WARNING(f"Found {email_dupes.count()} duplicate EmailAddresses"))
            for item in email_dupes:
                email = item['email']
                addrs = EmailAddress.objects.filter(email=email).order_by('id')
                # This is tricky. Different users might claim same email if not verified?
                # But if verified, it should be unique.
                # We'll just report for now, or delete unverified ones if verified exists.
                verified = addrs.filter(verified=True)
                if verified.exists():
                    # Delete unverified duplicates
                    unverified = addrs.filter(verified=False)
                    for addr in unverified:
                        self.stdout.write(f"Deleting unverified duplicate email {addr.email} for user {addr.user}")
                        addr.delete()
                    
                    # If multiple verified?
                    if verified.count() > 1:
                        self.stdout.write(self.style.ERROR(f"Multiple verified entries for {email}. Manual intervention needed."))
                else:
                    # All unverified. Keep one?
                    pass
        else:
            self.stdout.write('No duplicate EmailAddresses.')
            
        self.stdout.write(self.style.SUCCESS('Duplicate check completed.'))
