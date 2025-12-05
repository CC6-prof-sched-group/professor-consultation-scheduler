"""Compatibility wrapper for display_name.

This thin wrapper delegates to the canonical implementation in
`apps.accounts.templatetags.user_extras` so we keep backwards
compatibility if templates import this module path. Prefer the
implementation under `apps.accounts`.
"""

from django import template

register = template.Library()

try:
    # import the real implementation
    from apps.accounts.templatetags.user_extras import display_name as _display_name
except Exception:
    _display_name = None


@register.filter(is_safe=False)
def display_name(user):
    if _display_name is None:
        return ''
    return _display_name(user)
