from django import template
from django.utils.html import conditional_escape

register = template.Library()

try:
    from allauth.socialaccount.models import SocialAccount
except Exception:
    SocialAccount = None


@register.filter(is_safe=False)
def display_name(user):
    """Return the best display name for a user.

    Priority:
    1. user.get_full_name() if set
    2. SocialAccount.extra_data['name'] (Google) if available
    3. user.username if available
    4. user.email as fallback
    """
    if not user:
        return ''

    try:
        full = user.get_full_name()
        if full:
            return conditional_escape(full)
    except Exception:
        pass

    try:
        if SocialAccount is not None:
            sa_list = None
            if hasattr(user, '_prefetched_objects_cache') and 'socialaccount_set' in user._prefetched_objects_cache:
                sa_list = user._prefetched_objects_cache['socialaccount_set']
            else:
                sa_list = SocialAccount.objects.filter(user=user, provider='google')

            if sa_list:
                sa = sa_list[0] if hasattr(sa_list, '__getitem__') and len(sa_list) > 0 else None
                if sa:
                    extra = getattr(sa, 'extra_data', {}) or {}
                    name = extra.get('name') or None
                    if not name:
                        given = extra.get('given_name')
                        family = extra.get('family_name')
                        if given and family:
                            name = f"{given} {family}"
                    if name:
                        return conditional_escape(name)
    except Exception:
        pass

    try:
        if getattr(user, 'username', None):
            return conditional_escape(user.username)
    except Exception:
        pass

    try:
        return conditional_escape(user.email or '')
    except Exception:
        return ''
