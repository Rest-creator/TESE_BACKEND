# modules/listings/serializer/listing_serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from modules.listings.service.listing_service import ListingService

User = get_user_model()

class ListingImageReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    image_url = serializers.URLField()


class ListingReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    # Provide both seller (name) and sellerId (numeric) for frontend convenience
    seller = serializers.CharField()
    sellerId = serializers.IntegerField()

    listing_type = serializers.CharField()
    name = serializers.CharField()
    location = serializers.CharField()
    price = serializers.CharField()
    unit = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()

    # Optional fields depending on listing_type
    category = serializers.CharField(required=False, allow_null=True)
    organic = serializers.BooleanField(required=False, allow_null=True)
    provider = serializers.CharField(required=False, allow_null=True)
    supplier = serializers.CharField(required=False, allow_null=True)

    inquiries = serializers.IntegerField()
    views = serializers.IntegerField()
    images = ListingImageReadSerializer(many=True)

    @staticmethod
    def from_entity(entity):
        """
        Convert ListingEntity -> dict matching the serializer fields.
        Returns:
          - seller: human readable name (string)
          - sellerId: numeric user id (int) or None
        """
        # Default values
        seller_name = "Unknown Seller"
        seller_id = getattr(entity, "user_id", None)

        # Try to fetch a User record to build a nicer display name and confirm id
        try:
            if seller_id is not None:
                user = User.objects.get(id=seller_id)
                seller_id = user.id
                # Prefer full name, then business_name, then username, then phone_number
                if user.first_name or user.last_name:
                    seller_name = f"{user.first_name} {user.last_name}".strip()
                elif getattr(user, "business_name", None):
                    seller_name = user.business_name
                elif getattr(user, "username", None):
                    seller_name = user.username
                elif getattr(user, "phone_number", None):
                    seller_name = user.phone_number
            else:
                # If entity.user_id not set but entity has some other user ref, try to use it defensively
                # (keep seller_id None in that case)
                seller_name = "Unknown Seller"
        except User.DoesNotExist:
            # keep seller_name as default, but ensure seller_id is whatever entity had (may be None)
            seller_id = getattr(entity, "user_id", None)

        return {
            "id": entity.id,
            "seller": seller_name,
            "sellerId": seller_id,
            "listing_type": entity.listing_type,
            "name": entity.name,
            "location": entity.location,
            "price": entity.price,
            "unit": entity.unit,
            "description": entity.description,
            "status": entity.status,
            "category": getattr(entity, "category", None),
            "organic": getattr(entity, "organic", None),
            "provider": getattr(entity, "provider", None),
            "supplier": getattr(entity, "supplier", None),
            "inquiries": getattr(entity, "inquiries", 0),
            "views": getattr(entity, "views", 0),
            "images": [{"id": i.id, "image_url": i.image_url} for i in getattr(entity, "images", [])],
        }


class ListingWriteSerializer(serializers.Serializer):
    listing_type = serializers.ChoiceField(choices=["product", "service", "supplier_product"])
    name = serializers.CharField()
    location = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField(required=False, default="active")

    # Optional fields
    category = serializers.CharField(required=False, allow_null=True)
    organic = serializers.BooleanField(required=False, default=False)
    provider = serializers.CharField(required=False, allow_null=True)
    supplier = serializers.CharField(required=False, allow_null=True)

    # For uploads: images[] in multipart/form-data
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True
    )

    def create(self, validated_data):
        images = validated_data.pop("images", [])  # always a list
        user = self.context["request"].user
        entity = ListingService.create_listing(
            user_id=user.id,
            payload=validated_data,
            images_files=images
        )
        return ListingReadSerializer.from_entity(entity)

    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)  # None = don’t replace
        entity = ListingService.update_listing(
            listing_id=instance.id,
            user_id=self.context["request"].user.id,
            payload=validated_data,
            images_files=images
        )
        return ListingReadSerializer.from_entity(entity)
