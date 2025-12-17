from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.account.models import EmailAddress
from django.db.models import Count

User = get_user_model()

class Command(BaseCommand):
    help = 'Fixes duplicate accounts and email addresses that cause login errors'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up SocialApp configuration...')
        # 0. Delete all SocialApp entries (we rely on settings.py)
        count, _ = SocialApp.objects.all().delete()
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} SocialApp entries (using settings.py instead)"))
        else:
            self.stdout.write("No SocialApp entries found.")

        self.stdout.write('Checking for duplicates (Case-Insensitive)...')
        
        # 1. Check for duplicate emails in User model
        users = User.objects.all()
        email_map = {}
        for user in users:
            email = user.email.lower().strip()
            if not email:
                continue
            if email in email_map:
                email_map[email].append(user)
            else:
                email_map[email] = [user]
        
        for email, user_list in email_map.items():
            if len(user_list) > 1:
                self.stdout.write(self.style.WARNING(f"Found {len(user_list)} users with email '{email}'"))
                # Sort by date joined, keep oldest
                user_list.sort(key=lambda u: u.date_joined)
                primary = user_list[0]
                self.stdout.write(f"  Keeping primary: {primary.id} ({primary.email})")
                for duplicate in user_list[1:]:
                    self.stdout.write(f"  Deleting duplicate: {duplicate.id} ({duplicate.email})")
                    # Move social accounts to primary if needed?
                    # For now, just delete to clear the error.
                    duplicate.delete()
        
        # 2. Check for duplicate SocialAccounts
        # Group by (provider, uid)
        socials = SocialAccount.objects.all()
        social_map = {}
        for sa in socials:
            key = (sa.provider, sa.uid)
            if key in social_map:
                social_map[key].append(sa)
            else:
                social_map[key] = [sa]
                
        for key, sa_list in social_map.items():
            if len(sa_list) > 1:
                self.stdout.write(self.style.WARNING(f"Found {len(sa_list)} SocialAccounts for {key}"))
                # Keep one
                primary = sa_list[0]
                for duplicate in sa_list[1:]:
                    self.stdout.write(f"  Deleting duplicate SocialAccount: {duplicate.id}")
                    duplicate.delete()

        # 3. Check for duplicate EmailAddresses
        emails = EmailAddress.objects.all()
        e_map = {}
        for e in emails:
            email = e.email.lower().strip()
            if email in e_map:
                e_map[email].append(e)
            else:
                e_map[email] = [e]
                
        for email, e_list in e_map.items():
            if len(e_list) > 1:
                self.stdout.write(self.style.WARNING(f"Found {len(e_list)} EmailAddresses for '{email}'"))
                # Prefer verified
                verified = [e for e in e_list if e.verified]
                unverified = [e for e in e_list if not e.verified]
                
                if verified:
                    # Keep the first verified one
                    primary = verified[0]
                    # Delete all unverified
                    for d in unverified:
                        self.stdout.write(f"  Deleting unverified duplicate: {d.id}")
                        d.delete()
                    # Delete extra verified?
                    for d in verified[1:]:
                        self.stdout.write(f"  Deleting extra verified duplicate: {d.id}")
                        d.delete()
                else:
                    # Keep one unverified
                    primary = unverified[0]
                    for d in unverified[1:]:
                        self.stdout.write(f"  Deleting duplicate unverified: {d.id}")
                        d.delete()
            
        self.stdout.write(self.style.SUCCESS('Duplicate check completed.'))
