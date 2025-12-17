"""
Custom allauth adapter for ConsultEase.
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to customize allauth behavior.
    """
    
    def get_signup_redirect_url(self, request):
        """
        Redirect to login page after signup with success message.
        """
        messages.success(
            request, 
            'Account created successfully! Please sign in with your new credentials.'
        )
        return '/accounts/login/'
    
    def get_login_redirect_url(self, request):
        """
        Redirect to profile setup if user hasn't completed their profile.
        Otherwise redirect to home.
        """
        user = request.user
        if not user.profile_setup_completed:
            return '/profile/setup/'
        return '/'
