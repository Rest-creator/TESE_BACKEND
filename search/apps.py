# search/apps.py
from django.apps import AppConfig

class SearchConfig(AppConfig):
    name = "search"

    def ready(self):
        from django.db.models.signals import post_save, post_delete
        from django.dispatch import receiver
        from .models import SearchIndexEntry
        from .services.search_services import index_object, delete_object_from_index

        # Automatically index any model that has to_search_document
        from django.apps import apps
        for model in apps.get_models():
            if hasattr(model, "to_search_document"):
                @receiver(post_save, sender=model)
                def auto_index(sender, instance, **kwargs):
                    index_object(instance)

                @receiver(post_delete, sender=model)
                def auto_delete(sender, instance, **kwargs):
                    delete_object_from_index(instance)
