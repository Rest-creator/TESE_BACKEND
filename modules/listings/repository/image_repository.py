from typing import List
from django.contrib.contenttypes.models import ContentType
from teseapi.models import ListingImage

class ImageRepository:

    @staticmethod
    def replace_images(obj, image_urls: List[str]):
        """
        obj: Product, SupplierProduct, or Service instance
        """
        ct = ContentType.objects.get_for_model(obj)
        ListingImage.objects.filter(content_type=ct, object_id=obj.id).delete()
        ListingImage.objects.bulk_create([
            ListingImage(content_object=obj, image_url=url) for url in image_urls
        ])
