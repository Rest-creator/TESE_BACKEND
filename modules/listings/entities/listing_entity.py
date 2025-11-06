# entities.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ListingImageEntity:
    id: int
    image_url: str


@dataclass
class ListingEntity:
    id: int
    user_id: int
    listing_type: str  # product | service | supplier_product
    name: str
    location: str
    price: str
    unit: str
    description: str
    status: str
    category: Optional[str] = None
    organic: Optional[bool] = None
    provider: Optional[str] = None
    supplier: Optional[str] = None
    inquiries: int = 0
    views: int = 0
    images: List[ListingImageEntity] = None

    @staticmethod
    def from_model(listing):
        images = [
            ListingImageEntity(id=img.id, image_url=img.image_url)
            for img in listing.images.all()
        ]
        return ListingEntity(
            id=listing.id,
            user_id=listing.user_id,
            listing_type=listing.listing_type,
            name=listing.name,
            location=listing.location,
            price=str(listing.price),
            unit=listing.unit,
            description=listing.description,
            status=listing.status,
            category=listing.category,
            organic=listing.organic,
            provider=listing.provider,
            supplier=listing.supplier,
            inquiries=getattr(listing, "inquiries", 0),  # default if missing
            views=getattr(listing, "views", 0),          # default if missing
            images=images,
        )
