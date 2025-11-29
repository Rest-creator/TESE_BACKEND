from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .services.search_services import index_object, delete_object_from_index

from teseapi.models import Listing 


@receiver(post_save, sender=Listing)
def auto_index_listing(sender, instance, **kwargs):
    """
    Triggered whenever a Listing is created or updated.
    """
    index_object(instance)

@receiver(post_delete, sender=Listing)
def auto_delete_listing_index(sender, instance, **kwargs):
    """
    Triggered whenever a Listing is deleted.
    """
    delete_object_from_index(instance)