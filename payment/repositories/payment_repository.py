# infrastructure/repositories/payment_repository.py
from typing import List, Optional
from django.db import transaction
from ..entities.payment_entity import CartItemEntity, OrderEntity, PaymentEntity
from teseapi.models import CartItem, Order, Payment, Listing


class CartRepository:

    def add_item(
        self, user_id: int, listing_id: int, quantity: int, price: float
    ) -> CartItemEntity:
        """
        Adds an item to the cart. If it exists, increments quantity.
        """
        try:
            listing = Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            raise ValueError(f"Listing with ID {listing_id} not found.")

        cart_item, created = CartItem.objects.get_or_create(
            user_id=user_id,
            listing=listing,
            defaults={"quantity": quantity, "price": price},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return CartItemEntity(
            id=cart_item.id,
            user_id=cart_item.user_id,
            quantity=cart_item.quantity,
            price=float(cart_item.price),
        )

    def get_user_cart(self, user_id: int) -> List[CartItemEntity]:
        items = CartItem.objects.filter(user_id=user_id).select_related('listing')
        return [
            CartItemEntity(
                id=i.id,
                user_id=i.user_id,
                content_object=i.listing,  # Use the FK
                quantity=i.quantity,
                price=float(i.price),
            )
            for i in items
        ]

    def clear_cart(self, user_id: int):
        CartItem.objects.filter(user_id=user_id).delete()

    def remove_item(self, user_id: int, item_id: int):
        CartItem.objects.filter(id=item_id, user_id=user_id).delete()

    def update_item_quantity(self, user_id: int, item_id: int, quantity: int) -> Optional[CartItemEntity]:
        try:
            cart_item = CartItem.objects.get(id=item_id, user_id=user_id)
        except CartItem.DoesNotExist:
            raise ValueError("Cart item not found.")

        if quantity <= 0:
            cart_item.delete()
            return None

        cart_item.quantity = quantity
        cart_item.save()

        return CartItemEntity(
            id=cart_item.id,
            user_id=cart_item.user_id,
            content_object=cart_item.listing,  # Use the FK
            quantity=cart_item.quantity,
            price=float(cart_item.price),
        )



class OrderRepository:

    def create(self, user_id, items=None, total_amount=0, shipping_info=None, status="PENDING", payment_method="stripe"):
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status=status,
            payment_method=payment_method,
            shipping_info=shipping_info  # assign directly, not call
        )
        order.save()

        if items:
            order.items = items  # assuming you added JSONField: items = models.JSONField(null=True, blank=True)
            order.save(update_fields=["items"])

        return order


    def get_by_id(self, order_id):
        return Order.objects.get(id=order_id)


    def update_status(self, order_id: int, status: str):
        Order.objects.filter(id=order_id).update(status=status)


class PaymentRepository:

    def create(self, order_id: int, amount: float, method: str, status: str, transaction_ref: str = None) -> PaymentEntity:
        pay = Payment.objects.create(
            order_id=order_id,
            amount=amount,
            method=method,
            status=status,
            transaction_ref=transaction_ref
        )
        return PaymentEntity(pay.id, pay.order_id, pay.amount, pay.method, pay.status, pay.transaction_ref, pay.created_at)

    def update_status(self, payment_id: int, status: str, transaction_ref: str = None):
        Payment.objects.filter(id=payment_id).update(status=status, transaction_ref=transaction_ref)
