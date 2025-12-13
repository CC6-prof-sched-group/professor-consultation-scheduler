"""Template tags for user display utilities."""

from django import template

register = template.Library()


@register.filter(name='display_name')
def display_name(user):
    """
    Returns the display name for a user.
    For students: first_name last_name
    For professors: Prof. first_name last_name
    """
    if not user:
        return "Unknown User"
    
    # Get first and last name
    first_name = getattr(user, 'first_name', '')
    last_name = getattr(user, 'last_name', '')
    
    # Build the name
    if first_name or last_name:
        full_name = f"{first_name} {last_name}".strip()
    else:
        full_name = user.email or user.username
    
    # Add prefix for professors
    if hasattr(user, 'role') and user.role == 'PROFESSOR':
        return f"Prof. {full_name}"
    
    return full_name