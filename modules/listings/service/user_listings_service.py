# services/user_listings_service.py
from teseapi.models import Listing
from ..entities.listing_entity import ListingEntity

class UserListingsService:
    """
    Service for fetching user listings from the unified Listing model.
    """

    @staticmethod
    def get_listings(user, listing_type: str = None):
        """
        Returns a list of ListingEntity objects for the given user.
        If listing_type is provided, filters by that type (product, service, supplier_product).
        """
        qs = Listing.objects.filter(user=user).order_by('-created_at')
        if listing_type:
            qs = qs.filter(listing_type=listing_type)
        
        return [ListingEntity.from_model(l) for l in qs]
