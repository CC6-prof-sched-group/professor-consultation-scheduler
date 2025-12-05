from django import template

register = template.Library()

try:
    from allauth.socialaccount.models import SocialAccount
except Exception:
    SocialAccount = None


@register.simple_tag
def user_avatar(user):
    """Return best avatar URL for a user or empty string.

    Prefers prefetched socialaccount_set to avoid extra DB queries.
    """
    if not user:
        return ''

    try:
        sa_list = None
        if hasattr(user, '_prefetched_objects_cache') and 'socialaccount_set' in user._prefetched_objects_cache:
            sa_list = user._prefetched_objects_cache['socialaccount_set']
        elif SocialAccount is not None:
            sa_list = SocialAccount.objects.filter(user=user, provider='google')
        if sa_list:
            sa = sa_list[0] if hasattr(sa_list, '__getitem__') and len(sa_list) > 0 else None
            if sa:
                extra = getattr(sa, 'extra_data', {}) or {}
                pic = extra.get('picture') or extra.get('image') or None
                if pic:
                    return pic
    except Exception:
        pass

    return ''
