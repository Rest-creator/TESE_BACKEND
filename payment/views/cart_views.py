from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from ..services.cart_services import CartService

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        items = CartService.list_cart_items(request.user)
        
        data = []
        for item in items:
            # 1. Fetch Image
            # We try to get the first image associated with the listing
            first_image = item.listing.images.first()
            image_url = first_image.image_url if first_image else None

            # 2. Fetch Seller
            # Prioritize specific supplier name, fallback to username, then generic
            seller_name = "Tese Market"
            if item.listing.supplier:
                seller_name = item.listing.supplier
            elif item.listing.user:
                # Try full name, fallback to username
                seller_name = item.listing.user.get_full_name() or item.listing.user.username

            data.append({
                "id": item.id,
                "listing_id": item.listing.id,
                "name": item.listing.name,
                "quantity": item.quantity,
                "price": float(item.price),
                # ✅ Added Fields
                "image": image_url,
                "seller": seller_name,
                "category": item.listing.category
            })

        return Response(data)

    def create(self, request):
        listing_id = request.data.get("listing_id")
        quantity = int(request.data.get("quantity", 1))
        price = request.data.get("price")

        try:
            cart_item = CartService.add_to_cart(request.user, listing_id, quantity, price)
            
            # Fetch details for the response so the UI updates immediately
            first_image = cart_item.listing.images.first()
            image_url = first_image.image_url if first_image else None
            
            seller_name = "Tese Market"
            if cart_item.listing.supplier:
                seller_name = cart_item.listing.supplier
            elif cart_item.listing.user:
                seller_name = cart_item.listing.user.get_full_name() or cart_item.listing.user.username

            return Response({
                "id": cart_item.id,
                "listing_id": cart_item.listing.id,
                "name": cart_item.listing.name,
                "quantity": cart_item.quantity,
                "price": float(cart_item.price),
                # ✅ Added Fields
                "image": image_url,
                "seller": seller_name
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        quantity = request.data.get("quantity")
        if quantity is None:
             return Response({"error": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartService.update_cart_item(request.user, pk, int(quantity))
            
            if not cart_item:
                return Response({"message": "Item removed"}, status=status.HTTP_204_NO_CONTENT)

            # Fetch details for response
            first_image = cart_item.listing.images.first()
            image_url = first_image.image_url if first_image else None
            
            seller_name = "Tese Market"
            if cart_item.listing.supplier:
                seller_name = cart_item.listing.supplier
            elif cart_item.listing.user:
                seller_name = cart_item.listing.user.get_full_name() or cart_item.listing.user.username

            return Response({
                "id": cart_item.id,
                "listing_id": cart_item.listing.id,
                "name": cart_item.listing.name,
                "quantity": cart_item.quantity,
                "price": float(cart_item.price),
                # ✅ Added Fields
                "image": image_url,
                "seller": seller_name
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            CartService.remove_from_cart(request.user, pk)
            return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        payment_method = request.data.get("payment_method", "stripe")
        shipping_info = request.data.get("shipping_info", None)
        try:
            order, payment = CartService.checkout(request.user, payment_method, shipping_info)
            return Response({
                "order_id": order.id,
                "total_amount": float(order.total_amount),
                "payment_id": payment.id,
                "payment_status": payment.status
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)