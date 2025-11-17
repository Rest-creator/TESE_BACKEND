from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from ..services.cart_services import CartService

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        items = CartService.list_cart_items(request.user)
        data = [{
            "id": item.id,
            "listing_id": item.listing.id,
            "name": item.listing.name,
            "quantity": item.quantity,
            "price": float(item.price)
        } for item in items]
        print(data)
        return Response(data)

    def create(self, request):
        listing_id = request.data.get("listing_id")
        quantity = int(request.data.get("quantity", 1))
        price = request.data.get("price")

        try:
            cart_item = CartService.add_to_cart(request.user, listing_id, quantity, price)
            return Response({
                "id": cart_item.id,
                "listing_id": cart_item.listing.id,
                "name": cart_item.listing.name,
                "quantity": cart_item.quantity,
                "price": float(cart_item.price)
            }, status=status.HTTP_201_CREATED)
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
