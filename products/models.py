from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from pgvector.django import VectorField


class Listing(models.Model):
    LISTING_TYPES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('supplier_product', 'Supplier Product'),
    ]

    # Common fields
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)]
    )  # NEW FIELD
    unit = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    category = models.CharField(max_length=100, blank=True, null=True)
    organic = models.BooleanField(null=True, blank=True, default=None)
    provider = models.CharField(max_length=255, blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    embedding = VectorField(null=True, blank=True)

    # Generic relations
    images = GenericRelation('ListingImage')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.listing_type.capitalize()}: {self.name} by {self.user.username}"

    def to_search_document(self):
        first_image = self.images.first().image_url if self.images.exists() else ""
        text_for_embedding = f"{self.name} {self.category or ''} {self.description or ''}"
        return {
            "id": self.id,
            "title": self.name,
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
            "embedding_text": text_for_embedding,
            "embedding": None,
        }


class ListingImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.content_object}"
