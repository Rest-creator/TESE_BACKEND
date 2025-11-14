from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings # Import settings to reference AUTH_USER_MODEL
from django.core.validators import MinValueValidator
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Import GenericForeignKey and GenericRelation
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation 
from django.contrib.contenttypes.models import ContentType
from pgvector.django import VectorField



class User(AbstractUser):
    location = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True, help_text="Short bio or description of the user.")
    business_name = models.CharField(max_length=255, blank=True, null=True)
    service_type = models.CharField(max_length=255, blank=True, null=True)
     # Consider making it unique if phone numbers are used for login/identification
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)

    
class Category(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    
    def __str__(self):
        return self.name
    
class Location(models.Model):
    region = models.CharField(max_length=250)
    district = models.CharField(max_length=250)
    
    def __str__(self):
        return f'{self.district} {self.region}'

# Create a single model for all listings
class Listing(models.Model):
    LISTING_TYPES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('supplier_product', 'Supplier Product'),
    ]
    
    # Common fields from ListingBase
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=50)
    description = models.TextField()
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Specific fields that may be null depending on type
    category = models.CharField(max_length=100, blank=True, null=True)
    organic = models.BooleanField(default=False, blank=True, null=True)
    provider = models.CharField(max_length=255, blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    embedding = VectorField(null=True, blank=True)
    
    # Generic Relations for images and cart items
    images = GenericRelation('ListingImage')
    cart_items = GenericRelation('CartItem')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.listing_type.capitalize()}: {self.name} by {self.user.username}"
    
    def to_search_document(self):
        """
        Combine title, description, and category for embeddings.
        """
        first_image = self.images.first().image_url if hasattr(self, "images") and self.images.exists() else ""
        text_for_embedding = f"{self.name} {self.category or ''} {self.description or ''}"

        return {
            "id": self.id,
            "title": self.name,
            "name": self.name,
            "price": float(self.price),
            "unit": self.unit,
            "image": first_image,
            "category": self.category or "",
            "seller": self.user.username,
            "sellerId": self.user_id,
            "location": self.location,
            "description": self.description or "",
            "status": self.status or "",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "embedding_text": text_for_embedding,  # used for embedding generation
            "embedding": None,
        }



class ListingImage(models.Model):
    """
    Model for images associated with Service and SupplierProduct listings,
    storing Bytescale CDN URLs.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    object_id = models.PositiveBigIntegerField()
    
    content_object = GenericForeignKey('content_type', 'object_id')

    # Change from ImageField to URLField to store Bytescale CDN URL
    image_url = models.URLField(max_length=500, default="...")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.content_object} - {self.image_url}"

    class Meta:
        verbose_name = "Listing Image"
        verbose_name_plural = "Listing Images"

# ***********************************************
# Payment Models
# ***********************************************

# marketplace/models.py
"""
These are Django ORM models backing our entities.
"""

from django.db import models
from django.conf import settings

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