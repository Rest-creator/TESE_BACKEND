from rest_framework import serializers
from ..models import Listing, ListingImage

class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image_url']

class ListingSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    # ✅ Add this field to resolve the name
    seller = serializers.SerializerMethodField()
    sellerId = serializers.SerializerMethodField() # Helpful for frontend navigation

    class Meta:
        model = Listing
        fields = [
            'id', 'listing_type', 'user', 'name', 'location', 'price', 'unit',
            'description', 'status', 'category', 'organic', 'provider', 'supplier',
            'images', 'created_at', 'updated_at', 
            'seller', 'sellerId' # ✅ Include new fields
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_seller(self, obj):
        """
        Returns the display name for the seller.
        Priority: 
        1. 'supplier' field (if type=supplier_product)
        2. 'provider' field (if type=service)
        3. User's full name
        4. User's username
        """
        if obj.listing_type == 'supplier_product' and obj.supplier:
            return obj.supplier
        
        if obj.listing_type == 'service' and obj.provider:
            return obj.provider
            
        # Fallback to User model
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
            
        return "Unknown Seller"

    def get_sellerId(self, obj):
        """
        Returns the User ID for linking to profiles/chats.
        """
        return obj.user.id if obj.user else None