from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .services.search_services import index_object, delete_object_from_index

from teseapi.models import Listing 

INDEXABLE_MODELS = [Listing]

@receiver(post_save, sender=INDEXABLE_MODELS)
def auto_index_on_save(sender, instance, **kwargs):
    """
    Automatically index any model in INDEXABLE_MODELS when saved.
    (Implements SR-07)
    """
    # TODO: Convert this to a background task!
    # index_object.delay(instance)  # <-- Example for Celery
    index_object(instance)  # Synchronous version

@receiver(post_delete, sender=INDEXABLE_MODELS)
def auto_delete_from_index_on_delete(sender, instance, **kwargs):
    """
    Automatically remove from index when deleted.
    (Implements SR-07)
    """
    # TODO: Convert to background task
    delete_object_from_index(instance)