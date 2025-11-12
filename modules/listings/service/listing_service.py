# services/listing_service.py
from typing import List, Optional
from django.db import transaction
from ..repository.listing_repository import ListingRepository
from ..repository.image_repository import ImageRepository
from ..entities.listing_entity import ListingEntity
# CHANGED: Import the new S3Client
from modules.utils.s3_client import S3Client


class ListingService:

    FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1527847263472-aa5338d178b8?w=500&auto:format&fit:crop&q=60"

    @staticmethod
    @transaction.atomic
    def create_listing(user_id: int, payload: dict, images_files: Optional[List] = None) -> ListingEntity:
        listing_data = {
            "user_id": user_id,
            "listing_type": payload["listing_type"],
            "name": payload["name"],
            "location": payload["location"],
            "price": payload["price"],
            "unit": payload["unit"],
            "description": payload["description"],
            "status": payload.get("status", "active"),
            "category": payload.get("category"),
            "organic": payload.get("organic", False),
            "provider": payload.get("provider"),
            "supplier": payload.get("supplier"),
        }
        listing = ListingRepository.create(listing_data)

        if images_files:
            # CHANGED: Call the new S3 upload method
            urls = ListingService._upload_to_s3(images_files)
            ImageRepository.replace_images(listing, urls)

        return listing

    @staticmethod
    @transaction.atomic
    def update_listing(listing_id: int, user_id: int, payload: dict, images_files: Optional[List] = None) -> ListingEntity:
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise ValueError("Listing not found")
        if listing.user_id != user_id:
            raise PermissionError("Not authorized")

        allowed_fields = ["name", "location", "price", "unit", "description", "status", "category", "organic", "provider", "supplier", "listing_type"]
        update_data = {k: v for k, v in payload.items() if k in allowed_fields}
        listing = ListingRepository.update(listing, update_data)

        if images_files is not None:
            urls = ListingService._upload_to_s3(images_files)
            ImageRepository.replace_images(listing, urls)

        return listing

    @staticmethod
    def list_listings(user_id: Optional[int] = None, listing_type: Optional[str] = None) -> List[ListingEntity]:
        if user_id:
            qs = ListingRepository.list_by_user(user_id)
        elif listing_type:
            qs = ListingRepository.list_by_type(listing_type)
        else:
            qs = ListingRepository.list_all()
        return [ListingEntity.from_model(l) for l in qs]

    @staticmethod
    @transaction.atomic
    def delete_listing(listing_id: int, user_id: int) -> None:
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise ValueError("Listing not found")
        if listing.user_id != user_id:
            raise PermissionError("Not authorized to delete this listing")
        ListingRepository.delete(listing)

    @staticmethod
    # CHANGED: Renamed method
    def _upload_to_s3(images_files) -> List[str]:
        urls = []
        if not images_files:
            return [ListingService.FALLBACK_IMAGE_URL]
        
        for f in images_files:
                f.seek(0)
                content = f.read()
                # CHANGED: Use the S3Client
                url = S3Client.upload_file(
                    file_name=f.name,
                    file_content=content,
                    content_type=getattr(f, "content_type", "application/octet-stream")
                )
                urls.append(url)
        

        return urls if urls else [ListingService.FALLBACK_IMAGE_URL]