# TESE Marketplace - Development Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Coding Standards](#coding-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Git Workflow](#git-workflow)
6. [Debugging](#debugging)
7. [Contributing](#contributing)

---

## Getting Started

### Development Environment Setup

#### 1. Prerequisites

**Required:**
- Python 3.9 or higher
- Git
- Code editor (VS Code recommended)
- PostgreSQL (optional for development)
- Redis (for WebSocket features)

**Recommended VS Code Extensions:**
- Python (Microsoft)
- Django (Baptiste Darthenay)
- Pylance
- GitLens
- REST Client
- SQLite Viewer

#### 2. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd Tese-Marketplace/Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
# Or manually install:
pip install black flake8 pytest pytest-django ipython django-debug-toolbar
```

#### 3. Configure Development Settings

Create `.env` file:

```env
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Use SQLite for development
DATABASE_URL=sqlite:///db.sqlite3

# Development keys (use test keys)
BYTESCALE_API_KEY=public_test_key
STRIPE_SECRET_KEY=sk_test_your_test_key
PAYNOW_INTEGRATION_ID=test_id
PAYNOW_SECRET_KEY=test_key
```

#### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: (choose a password)

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

#### 5. Run Development Server

```bash
# Start Django server
python manage.py runserver

# Open browser to:
# - API: http://localhost:8000/api/
# - Admin: http://localhost:8000/admin/
```

---

## Development Workflow

### Project Structure Best Practices

```
Backend/
├── docs/                      # Documentation
├── modules/                   # Feature modules
│   ├── auth/
│   │   ├── entities/         # Domain models
│   │   ├── repositories/     # Data access
│   │   ├── serializers/      # API serializers
│   │   └── services/         # Business logic
│   ├── listings/
│   ├── messaging/
│   └── payment_module/
├── search/                    # Search module
├── teseapi/                   # Main API app
│   ├── views_app/            # View controllers
│   ├── models.py             # Database models
│   └── urls.py               # URL routing
├── teseapp/                   # Project settings
├── manage.py
└── requirements.txt
```

### Adding a New Feature

#### Step 1: Create Module Structure

```bash
# Create new module
mkdir -p modules/new_feature/{entities,repositories,serializers,services}
touch modules/new_feature/__init__.py
```

#### Step 2: Define Entity

```python
# modules/new_feature/entities/feature_entity.py
class FeatureEntity:
    """Domain entity for the feature"""
    
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        self.metadata = kwargs
    
    @classmethod
    def from_model(cls, model_instance):
        """Convert Django model to entity"""
        return cls(
            id=model_instance.id,
            name=model_instance.name,
            # ... other fields
        )
    
    def to_dict(self):
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            **self.metadata
        }
```

#### Step 3: Create Repository

```python
# modules/new_feature/repositories/feature_repository.py
from teseapi.models import FeatureModel

class FeatureRepository:
    """Data access layer for Feature"""
    
    @staticmethod
    def get_all():
        """Retrieve all features"""
        return FeatureModel.objects.all()
    
    @staticmethod
    def get_by_id(feature_id):
        """Retrieve feature by ID"""
        return FeatureModel.objects.filter(id=feature_id).first()
    
    @staticmethod
    def create(data):
        """Create new feature"""
        return FeatureModel.objects.create(**data)
    
    @staticmethod
    def update(feature_id, data):
        """Update existing feature"""
        return FeatureModel.objects.filter(id=feature_id).update(**data)
    
    @staticmethod
    def delete(feature_id):
        """Delete feature"""
        return FeatureModel.objects.filter(id=feature_id).delete()
```

#### Step 4: Implement Service

```python
# modules/new_feature/services/feature_service.py
from ..repositories.feature_repository import FeatureRepository
from ..entities.feature_entity import FeatureEntity

class FeatureService:
    """Business logic for Feature"""
    
    @staticmethod
    def get_all_features():
        """Get all features with business logic"""
        features = FeatureRepository.get_all()
        return [FeatureEntity.from_model(f) for f in features]
    
    @staticmethod
    def create_feature(user, data):
        """Create feature with validation"""
        # Validation
        if not data.get('name'):
            raise ValueError("Name is required")
        
        # Business rules
        data['created_by'] = user
        
        # Create via repository
        feature = FeatureRepository.create(data)
        
        # Post-creation tasks
        # e.g., send notification, index for search
        
        return FeatureEntity.from_model(feature)
    
    @staticmethod
    def update_feature(feature_id, user, data):
        """Update feature with authorization"""
        feature = FeatureRepository.get_by_id(feature_id)
        
        # Authorization check
        if feature.created_by != user:
            raise PermissionError("Not authorized")
        
        # Update
        FeatureRepository.update(feature_id, data)
        
        return FeatureEntity.from_model(
            FeatureRepository.get_by_id(feature_id)
        )
```

#### Step 5: Create Serializer

```python
# modules/new_feature/serializers/feature_serializers.py
from rest_framework import serializers
from teseapi.models import FeatureModel

class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature API"""
    
    class Meta:
        model = FeatureModel
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Custom validation for name field"""
        if len(value) < 3:
            raise serializers.ValidationError(
                "Name must be at least 3 characters"
            )
        return value
```

#### Step 6: Create Views

```python
# teseapi/views_app/feature_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from modules.new_feature.services.feature_service import FeatureService
from modules.new_feature.serializers.feature_serializers import FeatureSerializer

class FeatureListCreateView(APIView):
    """List and create features"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all features"""
        features = FeatureService.get_all_features()
        serializer = FeatureSerializer(
            [f.to_dict() for f in features], 
            many=True
        )
        return Response(serializer.data)
    
    def post(self, request):
        """Create new feature"""
        serializer = FeatureSerializer(data=request.data)
        
        if serializer.is_valid():
            feature = FeatureService.create_feature(
                request.user,
                serializer.validated_data
            )
            return Response(
                FeatureSerializer(feature.to_dict()).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
```

#### Step 7: Register URLs

```python
# teseapi/urls.py
from .views_app.feature_views import FeatureListCreateView

urlpatterns = [
    # ... existing patterns
    path('features/', FeatureListCreateView.as_view(), name='feature-list-create'),
]
```

#### Step 8: Write Tests

```python
# modules/new_feature/tests/test_feature.py
from django.test import TestCase
from modules.new_feature.services.feature_service import FeatureService

class FeatureServiceTest(TestCase):
    def test_create_feature(self):
        """Test feature creation"""
        data = {'name': 'Test Feature'}
        feature = FeatureService.create_feature(self.user, data)
        self.assertEqual(feature.name, 'Test Feature')
```

---

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these specifics:

#### 1. Imports

```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
from django.db import models
from rest_framework import serializers

# Local imports
from .models import User
from ..services import AuthService
```

#### 2. Naming Conventions

```python
# Classes: PascalCase
class UserRepository:
    pass

# Functions/methods: snake_case
def create_user(data):
    pass

# Constants: UPPERCASE
MAX_UPLOAD_SIZE = 5242880

# Variables: snake_case
user_count = 10
```

#### 3. Code Formatting

```python
# Line length: max 100 characters
def long_function_name(
    parameter_one, parameter_two, parameter_three,
    parameter_four, parameter_five
):
    """Docstring explaining the function"""
    pass

# Whitespace
x = 1  # Good
x=1    # Bad

# List comprehensions
result = [
    item.process()
    for item in items
    if item.is_valid()
]
```

#### 4. Docstrings

```python
def calculate_total(items, tax_rate=0.1):
    """
    Calculate total price including tax.
    
    Args:
        items (list): List of items with price attribute
        tax_rate (float): Tax rate as decimal (default: 0.1)
    
    Returns:
        Decimal: Total price including tax
    
    Raises:
        ValueError: If items list is empty
    
    Example:
        >>> items = [Item(price=10), Item(price=20)]
        >>> calculate_total(items)
        Decimal('33.00')
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

### Django-Specific Guidelines

#### 1. Model Design

```python
class Product(models.Model):
    """Model representing a product listing"""
    
    # Fields ordered: required, optional, dates
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Products"
    
    def __str__(self):
        return self.name
```

#### 2. QuerySet Optimization

```python
# Bad: N+1 queries
products = Product.objects.all()
for product in products:
    print(product.user.username)  # Extra query per product

# Good: Use select_related
products = Product.objects.select_related('user').all()
for product in products:
    print(product.user.username)  # No extra queries

# Good: Use prefetch_related for reverse FK
products = Product.objects.prefetch_related('images').all()
```

#### 3. Serializer Best Practices

```python
class ProductSerializer(serializers.ModelSerializer):
    # Computed fields
    total_price = serializers.SerializerMethodField()
    
    # Nested serializers
    user = UserBasicSerializer(read_only=True)
    
    # Write-only fields
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'total_price', 'user']
        read_only_fields = ['id', 'created_at']
    
    def get_total_price(self, obj):
        """Calculate total with tax"""
        return obj.price * 1.1
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── test_models.py
├── test_services.py
├── test_views.py
└── test_integration.py
```

### Unit Tests

```python
# modules/listings/tests/test_services.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from modules.listings.services.listing_service import ListingService

User = get_user_model()

class ListingServiceTest(TestCase):
    """Test cases for ListingService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            location='Test City'
        )
    
    def test_create_listing_success(self):
        """Test successful listing creation"""
        data = {
            'listing_type': 'product',
            'name': 'Test Product',
            'price': 10.00,
            'unit': 'kg',
            'location': 'Harare',
            'description': 'Test description'
        }
        
        listing = ListingService.create_listing(self.user, data)
        
        self.assertEqual(listing.name, 'Test Product')
        self.assertEqual(listing.user, self.user)
        self.assertEqual(listing.status, 'active')
    
    def test_create_listing_invalid_price(self):
        """Test listing creation with invalid price"""
        data = {
            'listing_type': 'product',
            'name': 'Test Product',
            'price': -10.00,  # Invalid
            'unit': 'kg',
            'location': 'Harare'
        }
        
        with self.assertRaises(ValueError):
            ListingService.create_listing(self.user, data)
```

### API Tests

```python
# tests/test_views.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ListingAPITest(APITestCase):
    """Test cases for Listing API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            location='Test City'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_listings(self):
        """Test GET /api/listings/"""
        url = reverse('listing-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_create_listing(self):
        """Test POST /api/listings/"""
        url = reverse('listing-list-create')
        data = {
            'listing_type': 'product',
            'name': 'Test Product',
            'price': '10.00',
            'unit': 'kg',
            'location': 'Harare',
            'description': 'Test'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Product')
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test modules.listings.tests.test_services

# Run specific test class
python manage.py test modules.listings.tests.test_services.ListingServiceTest

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## Git Workflow

### Branch Strategy

```
main (production)
  ├── develop (integration)
  │   ├── feature/user-authentication
  │   ├── feature/payment-gateway
  │   └── feature/search-optimization
  ├── hotfix/critical-bug-fix
  └── release/v1.0.0
```

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```bash
git commit -m "feat(listings): add image upload functionality"
git commit -m "fix(auth): resolve token refresh issue"
git commit -m "docs(api): update authentication endpoints"
```

### Development Workflow

```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. Make changes and commit
git add .
git commit -m "feat(module): add new feature"

# 3. Push to remote
git push origin feature/new-feature

# 4. Create Pull Request
# - Go to GitHub/GitLab
# - Create PR from feature/new-feature to develop
# - Request code review

# 5. After approval, merge
git checkout develop
git pull origin develop
git merge feature/new-feature
git push origin develop

# 6. Delete feature branch
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

## Debugging

### Django Debug Toolbar

```python
# settings.py (development only)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

### Using Django Shell

```bash
python manage.py shell
```

```python
# Import models
from teseapi.models import Listing, User

# Query data
listings = Listing.objects.all()
user = User.objects.get(username='admin')

# Test services
from modules.listings.services.listing_service import ListingService
result = ListingService.create_listing(user, data)

# Test search
from search.services.search_services import search_by_vector
results = search_by_vector("fresh vegetables")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
```

### Common Debugging Commands

```bash
# Check for errors
python manage.py check

# View SQL queries
python manage.py shell
>>> from django.db import connection
>>> connection.queries

# Debug authentication
python manage.py shell
>>> from django.contrib.auth import authenticate
>>> user = authenticate(username='admin', password='password')
>>> print(user)
```

---

## Contributing

### Pull Request Process

1. **Fork & Clone**
   ```bash
   git clone <your-fork-url>
   cd Tese-Marketplace/Backend
   ```

2. **Create Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Follow coding standards
   - Add tests
   - Update documentation

4. **Test**
   ```bash
   python manage.py test
   flake8 .
   black --check .
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

6. **Push & PR**
   ```bash
   git push origin feature/amazing-feature
   # Create PR on GitHub
   ```

### Code Review Checklist

**For Authors:**
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.log or debug code
- [ ] Migrations included (if needed)
- [ ] PR description is clear

**For Reviewers:**
- [ ] Code is readable and maintainable
- [ ] Tests cover new functionality
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

---

## Useful Commands

### Django Management Commands

```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Users
python manage.py createsuperuser
python manage.py changepassword <username>

# Data
python manage.py loaddata <fixture>
python manage.py dumpdata <app> > fixture.json

# Static files
python manage.py collectstatic
python manage.py findstatic <file>

# Shell
python manage.py shell
python manage.py shell_plus  # django-extensions

# Testing
python manage.py test
python manage.py test --keepdb  # Keep test database
```

### Code Quality Tools

```bash
# Format code
black .

# Check style
flake8 .

# Sort imports
isort .

# Type checking
mypy .

# Security check
bandit -r .
```

---

*Last Updated: 2024*
*Development Guide Version: 1.0.0*
