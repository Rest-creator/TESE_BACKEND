from decimal import Decimal
from django.core.exceptions import ValidationError
from ..models import CartItem, Order, Payment
from products.models import Listing
from django.db import transaction

class CartService:

    @staticmethod
    def add_to_cart(user, listing_id, quantity, price=None):
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise ValidationError("Listing does not exist.")

        # Ensure price is valid Decimal
        try:
            price_decimal = Decimal(price) if price is not None else listing.price
        except:
            raise ValidationError("Invalid price format.")

        # Create or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            user=user, listing=listing,
            defaults={'quantity': quantity, 'price': price_decimal}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.price = price_decimal
            cart_item.save()
        return cart_item

    @staticmethod
    def remove_from_cart(user, cart_item_id):
        try:
            cart_item = CartItem.objects.get(id=cart_item_id, user=user)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            raise ValidationError("Cart item does not exist.")

    @staticmethod
    def list_cart_items(user):
        return CartItem.objects.filter(user=user).select_related("listing")
    
    @staticmethod
    def update_cart_item(user, item_id, quantity):
        """
        Updates the quantity of a specific cart item.
        If quantity <= 0, deletes the item.
        """
        try:
            item = CartItem.objects.get(id=item_id, user=user)
            
            if quantity <= 0:
                item.delete()
                return None
            
            item.quantity = quantity
            item.save()
            return item
        except CartItem.DoesNotExist:
            raise Exception("Cart item not found")


    @staticmethod
    @transaction.atomic
    def checkout(user, payment_method="stripe", shipping_info=None):
        cart_items = CartItem.objects.filter(user=user)
        if not cart_items.exists():
            raise ValidationError("Cart is empty.")

        total_amount = sum(item.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status="PENDING",
            payment_method=payment_method,
            shipping_info=shipping_info,
            items=[{
                "listing_id": item.listing.id,
                "name": item.listing.name,
                "quantity": item.quantity,
                "price": float(item.price)
            } for item in cart_items]
        )

        # Here you would integrate real payment logic (Stripe, Ecocash, PayPal)
        # For now, we create a placeholder payment
        payment = Payment.objects.create(
            order=order,
            amount=total_amount,
            method=payment_method,
            status="INITIATED"
        )

        # Clear cart
        cart_items.delete()

        return order, payment
