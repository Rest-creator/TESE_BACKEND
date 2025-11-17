# interfaces/views/payment_views.py
"""
API endpoints for cart, checkout, and payment confirmation.
"""

# from urllib import request
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..services.payment_services import PaymentService
from ..repositories.payment_repository import CartRepository, OrderRepository, PaymentRepository
from ..serializers.payment_serializers import CartItemSerializer, PaymentSerializer


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = PaymentService(CartRepository(), OrderRepository(), PaymentRepository())

    def create(self, request):
        """
        Add an item (product, service, etc.) to cart.
        Checks if item already exists and updates quantity, otherwise adds a new item.
        """
        print("1. Received data from frontend:", request.data)  # First print
        
        item_id = request.data.get("id")
        item_type = request.data.get("type")
        quantity = int(request.data.get("quantity", 1))
        price = request.data.get("price")
        category = request.data.get("category")

        if not item_id or not item_type or not price:
            print("1.1. Data validation failed.")
            return Response(
                {"detail": "Item ID, type, and price are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            print("2. Calling PaymentService.add_to_cart with:", {
                "user_id": request.user.id,
                "item_id": item_id,
                "item_type": item_type,
                "quantity": quantity,
                "price": price,
            })
            item = self.service.add_to_cart(request.user.id, item_id, item_type, quantity, price, category)
            
            print("3. PaymentService.add_to_cart successful. Item returned:", item)
            return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            print(f"ERROR: A ValueError occurred in the view: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(f"CRITICAL ERROR: An unexpected exception occurred in the view: {e}")
            return Response({"detail": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def list(self, request):
        """
        Retrieve all items in the authenticated user's cart.
        This method handles GET requests to /api/cart/.
        """
        print("Received GET request for cart items.")
        try:
            items = self.service.get_cart(request.user.id)
            print(f"Found {len(items)} cart items.")
            serializer = CartItemSerializer(items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"CRITICAL ERROR: An unexpected exception occurred while fetching cart items: {e}")
            return Response({"detail": "An internal server error occurred while fetching cart items."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def destroy(self, request, pk=None):
        """
        Remove a specific cart item by its ID.
        """
        # ... (your existing destroy method) ...
        self.service.remove_from_cart(request.user.id, int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def update(self, request, pk=None):
        """
        Update the quantity of a specific cart item.
        This method handles PUT/PATCH requests.
        """
        print(f"Received PUT request to update cart item {pk}.")
        
        quantity = request.data.get("quantity")
        if quantity is None:
            return Response(
                {"detail": "Quantity is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Call the service layer method to handle the business logic
            updated_item = self.service.update_cart_item_quantity(request.user.id, int(pk), int(quantity))
            
            # If the item was removed (quantity <= 0), return a 204 No Content
            if updated_item is None:
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            # Serialize the updated item and return a 200 OK response
            return Response(CartItemSerializer(updated_item).data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error updating cart item: {e}")
            return Response(
                {"detail": "An internal server error occurred while updating the cart item."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = PaymentService(CartRepository(), OrderRepository(), PaymentRepository())

    def create(self, request):
        """
        Create an Order + Payment record.
        Later this will call the gateway (Stripe, PayPal, EcoCash).
        """
        method = request.data.get("method", "mobile_money")
        payment = self.service.checkout(request.user.id, method)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """
        Confirm payment after gateway responds.
        This would normally be triggered by a webhook.
        """
        success = request.data.get("success", True)
        transaction_ref = request.data.get("transaction_ref")
        self.service.confirm_payment(pk, success, transaction_ref)
        return Response({"message": "Payment status updated"}, status=status.HTTP_200_OK)



class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = PaymentService(CartRepository(), OrderRepository(), PaymentRepository())
    

    def create(self, request):
        print(request.data)
        """
        Create an order, attach shipping + payment info,
        and process payment (for now only Stripe).
        """
        user = request.user
        shipping_info = request.data.get("shippingInfo", {})
        payment_method = request.data.get("paymentMethod", "stripe")
        payment_details = request.data.get("paymentDetails", {})

        if not shipping_info.get("name") or not shipping_info.get("address"):
            return Response({"error": "Shipping info is incomplete"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Create order + pending payment
        payment = self.service.checkout(user.id, payment_method, shipping_info)

        # Step 2: Handle Stripe payment now (others later)
        if payment_method == "stripe":
            stripe_token = payment_details.get("stripeToken") or payment_details.get("cardNumber")  # adjust per frontend
            if not stripe_token:
                return Response({"error": "Missing Stripe token"}, status=status.HTTP_400_BAD_REQUEST)

            result = self.service.pay_order_with_stripe(payment.id, stripe_token)

            if result["success"]:
                return Response(
                    {
                        "message": "Payment successful",
                        "transaction_ref": result["transaction_ref"],
                        "order": PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": result.get("error", "Payment failed")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if payment_method == "paynow":
            phone = payment_details.get("phone")
            mobile_method = payment_details.get("mobileMethod", "ecocash")  # 'ecocash' or 'onemoney'
            if not phone:
                return Response({"error": "Missing phone for mobile payment"}, status=status.HTTP_400_BAD_REQUEST)

            result = self.service.pay_order_with_paynow(payment.id, phone, mobile_method)

            if result.get("success"):
                return Response(
                    {
                        "message": "Mobile payment initiated",
                        "poll_url": result.get("poll_url"),
                        "instructions": result.get("instructions"),
                        "order": PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": result.get("message", "Paynow mobile payment failed")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"error": f"Unsupported payment method: {payment_method}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
        
        
        
        
        