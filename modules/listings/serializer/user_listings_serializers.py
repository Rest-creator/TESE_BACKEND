# serializers/user_listing_serializer.py
from rest_framework import serializers
from ..serializer.listing_serializers import ListingReadSerializer


class UserListingSerializer(serializers.Serializer):
    """
    Generic wrapper serializer for user listings.
    Works with the unified Listing model.
    """
    listing_type = serializers.CharField(read_only=True)
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        """
        Returns the serialized data using ListingReadSerializer.
        """
        return ListingReadSerializer(obj, context=self.context).data

    def to_representation(self, instance):
        """
        Include the listing_type alongside serialized data.
        """
        data = super().to_representation(instance)
        data['listing_type'] = getattr(instance, 'listing_type', 'unknown')
        return data
