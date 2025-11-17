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
from products.models import Listing


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

