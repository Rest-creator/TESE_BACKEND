# core/services/payment_service.py
from ..entities.payment_entity import PaymentEntity
from ..repositories.payment_repository import CartRepository, OrderRepository, PaymentRepository
from ..gateways.stripe_gateway import StripeGateway
from ..gateways.paynow_gateway import PaynowGateway


class PaymentService:
    def __init__(self, cart_repo: CartRepository, order_repo: OrderRepository, payment_repo: PaymentRepository):
        self.cart_repo = cart_repo
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.stripe = StripeGateway()  # <--- add this
        self.paynow = PaynowGateway()  # <--- add this

    def add_to_cart(self, user_id: int, item_id, item_type: str, quantity: int, price: str, category: str = None):
        """
        Add item to the cart (or update quantity if it exists).
        """
        # Convert price to float
        price = float(price)
        return self.cart_repo.add_item(user_id, item_id, quantity, price)

    # def add_to_cart(self, user_id: int, listing_id: int, quantity: int, price: float):
    #     """
    #     Add item to the cart (or update quantity if it exists).
    #     """
    #     return self.cart_repo.add_item(user_id, listing_id, quantity, price)

    def get_cart(self, user_id: int):
        """
        Return all items currently in the user's cart.
        """
        return self.cart_repo.get_user_cart(user_id)

    def update_cart_item_quantity(self, user_id: int, item_id: int, quantity: int):
        """
        Orchestrates updating a cart item's quantity.
        """
        return self.cart_repo.update_item_quantity(user_id, item_id, quantity)
    
    def remove_from_cart(self, user_id: int, item_id: int):
        """
        Orchestrates removing a cart item.
        """
        self.cart_repo.remove_item(user_id, item_id)
        


    def pay_order_with_stripe(self, order_id: int, stripe_token: str, currency: str = "usd"):
        # Fetch order
        order = self.order_repo.get_by_id(order_id)

        # Charge
        result = self.stripe.charge(amount=order.total_amount, currency=currency, source=stripe_token)

        if result["success"]:
            # Create payment record
            payment = self.payment_repo.create(
                order_id=order.id,
                amount=order.total_amount,
                method="stripe",
                status="SUCCESS",
                transaction_ref=result["transaction_ref"]
            )
            # Update order
            self.order_repo.update_status(order.id, "PAID")
        else:
            # Create failed payment
            payment = self.payment_repo.create(
                order_id=order.id,
                amount=order.total_amount,
                method="stripe",
                status="FAILED",
                transaction_ref=result.get("transaction_ref")
            )
            # Update order
            self.order_repo.update_status(order.id, "FAILED")

        return result


    def checkout(self, user_id, payment_method, shipping_info=None):
        # Step 1: Get cart items
        cart_items = self.cart_repo.get_user_cart(user_id)

        # Step 2: Convert to JSON-serializable list of dicts
        items = [
            {
                "item_id": item.id,
                "name": getattr(item.content_object, "name", "Unknown"),
                "price": float(item.price),
                "quantity": item.quantity,
                "type": getattr(item.content_object, "type", "general")
            }
            for item in cart_items
        ]

        # Step 3: Compute total amount
        total_amount = sum(item["price"] * item["quantity"] for item in items)

        # Step 4: Create order
        order = self.order_repo.create(
            user_id=user_id,
            items=items,  # must be JSONField
            total_amount=total_amount,
            shipping_info=shipping_info,
            payment_method=payment_method
        )

        return order
    
    
        # ------------------ PAYNOW integration ------------------
    def pay_order_with_paynow(self, order_id: int, phone: str, mobile_method: str = "ecocash") -> dict:
        """
        Trigger a Paynow mobile money push (Ecocash/Onemoney). Returns poll_url/instructions.
        """
        order = self.order_repo.get_by_id(order_id)
        email = getattr(order, "email", None) or getattr(getattr(order, "user", None), "email", None) or "noreply@localhost"
        amount = float(order.total_amount)
        reference = str(order.id)

        result = self.paynow.send_mobile_payment(reference=reference, email=email, amount=amount, phone=phone, mobile_method=mobile_method)


        if result.get("success"):
            poll_url = result.get("poll_url")
            instructions = result.get("instructions")
            self.payment_repo.create(
            order_id=order.id,
            amount=amount,
            method="paynow_mobile",
            status="PENDING",
            transaction_ref=None,
            metadata={"poll_url": poll_url, "instructions": instructions}
            )
            self.order_repo.update_status(order.id, "PENDING_PAYMENT")


        return result


    def reconcile_paynow(self, poll_url: str) -> dict:
        """
        Poll Paynow for the final status of a transaction and update DB accordingly.
        Input: poll_url (string) — you should retrieve this from your Payment record's metadata
        Returns the check result and updates payment & order records when appropriate.
        """
        status = self.paynow.check_status(poll_url)


        # status is expected to be a dict like {"paid": bool, "status": '...' }
        paid = status.get("paid") if isinstance(status, dict) else False
        txn_status = status.get("status") if isinstance(status, dict) else None


        # Find payment record by poll_url
        payment = self.payment_repo.get_by_poll_url(poll_url)
        if not payment:
            return {"success": False, "message": "payment record not found for poll_url", "status": status}


        if paid:
            # mark payment success
            self.payment_repo.update_status(payment.id, "SUCCESS")
            self.payment_repo.update_transaction_ref(payment.id, txn_status or "paid")
            self.order_repo.update_status(payment.order_id, "PAID")
            return {"success": True, "message": "Payment completed", "status": status}
        else:
            # could be pending or failed
            new_status = "PENDING" if txn_status and txn_status.lower() in ("pending",) else "FAILED"
            self.payment_repo.update_status(payment.id, new_status)
            if new_status == "FAILED":
                self.order_repo.update_status(payment.order_id, "FAILED")
                return {"success": False, "message": "Payment not completed", "status": status}
