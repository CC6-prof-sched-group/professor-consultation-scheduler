"""
Signals for professor profile updates.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.consultations.models import Consultation


@receiver(post_save, sender=Consultation)
def update_professor_rating_on_save(sender, instance, created, **kwargs):
    """Update professor rating when consultation is rated."""
    if instance.rating is not None and hasattr(instance.professor, 'professor_profile'):
        instance.professor.professor_profile.calculate_ratings()


@receiver(post_delete, sender=Consultation)
def update_professor_rating_on_delete(sender, instance, **kwargs):
    """Update professor rating when consultation is deleted."""
    if instance.rating is not None and hasattr(instance.professor, 'professor_profile'):
        instance.professor.professor_profile.calculate_ratings()