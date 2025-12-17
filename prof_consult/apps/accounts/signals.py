from django.contrib.auth import logout
from django.dispatch import receiver
from allauth.account.signals import user_signed_up


@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    """Ensure a freshly signed-up user is not left authenticated.

    We only force a logout for regular (non-social) signups. Social
    signups (OAuth) include a `sociallogin` kwarg from allauth; those
    flows intentionally authenticate the user and should not be logged
    out here.
    """
    # If this signup was via a social provider, do nothing here
    if kwargs.get('sociallogin'):
        return

    try:
        logout(request)
    except Exception:
        # Best-effort: don't raise in signal handlers
        pass
