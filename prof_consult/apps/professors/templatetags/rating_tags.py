"""
Template tags for displaying ratings.
"""
from django import template

register = template.Library()


@register.inclusion_tag('components/star_rating.html')
def star_rating(rating, max_rating=5, show_number=True):
    """
    Display star rating.
    
    Usage: {% star_rating professor.average_rating %}
    """
    rating = float(rating) if rating else 0
    full_stars = int(rating)
    has_half_star = (rating - full_stars) >= 0.5
    empty_stars = max_rating - full_stars - (1 if has_half_star else 0)
    
    return {
        'rating': rating,
        'full_stars': range(full_stars),
        'has_half_star': has_half_star,
        'empty_stars': range(empty_stars),
        'show_number': show_number,
    }


@register.filter
def rating_class(rating):
    """Get CSS class for rating color."""
    rating = float(rating) if rating else 0
    if rating >= 4.5:
        return 'text-success'
    elif rating >= 3.5:
        return 'text-info'
    elif rating >= 2.5:
        return 'text-warning'
    else:
        return 'text-danger'


@register.filter
def rating_badge_class(rating):
    """Get badge class for rating."""
    rating = float(rating) if rating else 0
    if rating >= 4.5:
        return 'bg-success'
    elif rating >= 3.5:
        return 'bg-info'
    elif rating >= 2.5:
        return 'bg-warning'
    else:
        return 'bg-danger'
    
@register.filter
def multiply(value, arg):
    """Multiply two numbers."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0