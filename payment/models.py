from django.db import models
from django.conf import settings
from products.models import Listing

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Store price as string to avoid float precision issues
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        # Check if content_object exists before accessing name
        if self.listing:
            return f"{self.quantity} x {self.listing.name}"
        return f"{self.quantity} x [Deleted Listing]"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="PENDING")  # PENDING, PAID, FAILED
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default="stripe")  # stripe, paypal, ecocash, etc.
    shipping_info = models.JSONField(null=True, blank=True)  # Store shipping info as
    items = models.JSONField(null=True, blank=True)  # Store order items as JSON
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)  # e.g., Stripe PaymentIntent ID

     # Add a string representation for easier debugging
    def __str__(self):
        return f"Order {self.id} by {self.user.username} - {self.status}"


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # stripe, paypal, ecocash, etc.
    status = models.CharField(max_length=20, default="INITIATED")  # INITIATED, SUCCESS, FAILED
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order_id} - {self.status}"