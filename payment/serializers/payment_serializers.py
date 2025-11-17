from rest_framework import serializers
from ..entities.payment_entity import CartItemEntity
from teseapi.models import Payment

class CartItemSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    item_details = serializers.SerializerMethodField()

    def get_item_details(self, obj: CartItemEntity):
        """
        Return details about the listing (product/service/supplier_product) in the cart.
        """
        listing = getattr(obj, 'content_object', None)
        if not listing:
            return None

        # Determine type from listing_type field
        item_type = getattr(listing, 'listing_type', 'unknown')
        image_url = None
        if hasattr(listing, 'images') and listing.images.exists():
            image_url = listing.images.first().image_url

        seller_name = getattr(listing.user, 'business_name', None) or getattr(listing.user, 'username', 'N/A')

        details = {
            "id": listing.id,
            "name": getattr(listing, 'name', 'N/A'),
            "type": item_type,
            "image": image_url,
            "category": getattr(listing, 'category', 'N/A'),
            "seller": seller_name,
            "location": getattr(listing, 'location', None),
            "unit": getattr(listing, 'unit', None) if item_type == 'product' else None,
        }

        return details


class OrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField()
    total_amount = serializers.FloatField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()




class PaymentSerializer(serializers.ModelSerializer):
    # Map fields from related Order
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    total_amount = serializers.DecimalField(source='order.total_amount', max_digits=10, decimal_places=2, read_only=True)
    payment_method = serializers.CharField(source='order.payment_method', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order_id', 'total_amount', 'payment_method',
              'status', 'transaction_ref', 'created_at'
        ]

