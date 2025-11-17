from typing import List, Optional
from django.db import transaction
from ..models import Listing, ListingImage
from modules.utils.s3_client import S3Client

class ListingService:
    FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1527847263472-aa5338d178b8?w=500&auto=format&fit=crop&q=60"

    @staticmethod
    def get_listing_by_id(listing_id: int):
        try:
            return Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_listing(user, payload: dict, images_files: Optional[List] = None):
        organic = payload.get("organic")
        if isinstance(organic, str):
            organic = organic.lower() == "true"

        status = payload.get("status")
        if status not in ["active", "inactive"]:
            status = "active"  # default

        listing_type = payload.get("listing_type")
        if listing_type not in ["product", "service", "supplier_product"]:
            listing_type = "product"  # default if invalid or missing

        listing = Listing.objects.create(
            user=user,
            name=payload.get("name"),
            price=payload.get("price"),
            quantity=payload.get("quantity"),
            unit=payload.get("unit"),
            category=payload.get("category"),
            description=payload.get("description"),
            location=payload.get("location"),
            organic=organic,
            status=status,
            supplier=payload.get("supplier"),
            listing_type=listing_type,  # ✅ add this
            provider=payload.get("provider"),
        )



        if images_files:
            urls = ListingService._upload_to_s3(images_files)
            for url in urls:
                ListingImage.objects.create(content_object=listing, image_url=url)

        return listing

    @staticmethod
    @transaction.atomic
    def update_listing(listing, payload: dict, images_files=None, existing_images_to_keep=None):
        for key, value in payload.items():
            setattr(listing, key, value)
        listing.save()

        existing_images_to_keep = existing_images_to_keep or []
        
        if 'listing_type' in payload:
            listing_type = payload['listing_type']
            if listing_type in ["product", "service", "supplier_product"]:
                listing.listing_type = listing_type


        # Remove deleted images
        for img in listing.images.all():
            if img.image_url not in existing_images_to_keep:
                img.delete()

        # Upload new images
        if images_files:
            urls = ListingService._upload_to_s3(images_files)
            for url in urls:
                ListingImage.objects.create(content_object=listing, image_url=url)

        return listing

    @staticmethod
    @transaction.atomic
    def delete_listing(listing):
        listing.delete()

    @staticmethod
    def list_listings(user=None, listing_type=None):
        """
        Returns listings for the home page or filtered by user.

        - user=None → public/home page, return all listings
        - user=User → if `user_only=True`, return only this user's listings
        - listing_type → filter by product/service/supplier_product
        """
        qs = Listing.objects.all()

        if listing_type:
            qs = qs.filter(listing_type=listing_type)

        # Optionally, filter by user only if explicitly requested
        if user and getattr(user, "filter_by_user", False):
            qs = qs.filter(user=user)

        return qs

    @staticmethod
    def _upload_to_s3(images_files) -> List[str]:
        urls = []
        if not images_files:
            return [ListingService.FALLBACK_IMAGE_URL]

        for f in images_files:
            f.seek(0)
            content = f.read()
            url = S3Client.upload_file(
                file_name=f.name,
                file_content=content,
                content_type=getattr(f, "content_type", "application/octet-stream")
            )
            urls.append(url)
        return urls if urls else [ListingService.FALLBACK_IMAGE_URL]
