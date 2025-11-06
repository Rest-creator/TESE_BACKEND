# repositories.py
from typing import Optional
from django.db.models import QuerySet
from teseapi.models import Listing


class ListingRepository:
    @staticmethod
    def create(listing_data: dict) -> Listing:
        return Listing.objects.create(**listing_data)

    @staticmethod
    def update(listing: Listing, update_data: dict) -> Listing:
        for k, v in update_data.items():
            setattr(listing, k, v)
        listing.save()
        return listing

    @staticmethod
    def delete(listing: Listing) -> None:
        listing.delete()

    @staticmethod
    def get_by_id(listing_id: int) -> Optional[Listing]:
        return Listing.objects.filter(id=listing_id).select_related("user").prefetch_related("images").first()

    @staticmethod
    def list_all() -> QuerySet:
        return Listing.objects.all().select_related("user").prefetch_related("images")

    @staticmethod
    def list_by_user(user_id: int) -> QuerySet:
        return (
            Listing.objects.filter(user_id=user_id)
            .select_related("user")
            .prefetch_related("images")
        )

    @staticmethod
    def list_by_type(listing_type: str) -> QuerySet:
        """Return all listings of a specific type: product, service, supplier_product"""
        return (
            Listing.objects.filter(listing_type=listing_type)
            .select_related("user")
            .prefetch_related("images")
        )

    @staticmethod
    def increment_views(listing: Listing) -> None:
        Listing.objects.filter(id=listing.id).update(views=getattr(listing, "views", 0) + 1)
