# core/entities/payment.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from teseapi.models import CartItem, Order, Payment

@dataclass
class CartItemEntity:
    def __init__(self, id, user_id, quantity, price, content_object=None):
        self.id = id
        self.user_id = user_id
        self.quantity = quantity
        self.price = price
        self.content_object = content_object

@dataclass
class OrderEntity:
    id: Optional[int]
    user_id: int
    total_amount: float
    status: str  # PENDING, PAID, FAILED
    created_at: datetime

@dataclass
class PaymentEntity:
    id: Optional[int]
    order_id: int
    amount: float
    method: str  # "stripe", "paypal", "mobile_money"
    status: str  # INITIATED, SUCCESS, FAILED
    transaction_ref: Optional[str]
    created_at: datetime

# -----------------------
# Mapper functions
# -----------------------

def cart_item_to_entity(cart_item: CartItem) -> CartItemEntity:
    """
    Converts a CartItem ORM object to a CartItemEntity.
    """
    return CartItemEntity(
        id=cart_item.id,
        user_id=cart_item.user_id,
        listing=cart_item.listing,  # Pass the Listing object itself
        quantity=cart_item.quantity,
        price=float(cart_item.price),
    )

def order_to_entity(order: Order) -> OrderEntity:
    return OrderEntity(
        id=order.id,
        user_id=order.user_id,
        total_amount=float(order.total_amount),
        status=order.status,
        created_at=order.created_at,
    )

def payment_to_entity(payment: Payment) -> PaymentEntity:
    return PaymentEntity(
        id=payment.id,
        order_id=payment.order_id,
        amount=float(payment.amount),
        method=payment.method,
        status=payment.status,
        transaction_ref=payment.transaction_ref,
        created_at=payment.created_at,
    )
