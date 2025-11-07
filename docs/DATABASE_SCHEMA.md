# TESE Marketplace - Database Schema Documentation

## Table of Contents
1. [Database Overview](#database-overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Core Models](#core-models)
4. [Model Relationships](#model-relationships)
5. [Database Indexes](#database-indexes)
6. [Migrations](#migrations)
7. [Query Patterns](#query-patterns)

---

## Database Overview

### Database Systems

**Development:**
- **Engine**: SQLite 3
- **Location**: `db.sqlite3`
- **Features**: File-based, zero configuration

**Production:**
- **Engine**: PostgreSQL
- **Extensions**: pgvector (for semantic search)
- **Connection**: SSL/TLS encrypted
- **Pooling**: Connection pooling enabled

### Schema Design Principles

1. **Normalization**: Database follows 3NF (Third Normal Form)
2. **Generic Relations**: ContentType framework for polymorphic relationships
3. **Soft Deletes**: Status fields instead of hard deletes (where applicable)
4. **Timestamps**: All models track creation and modification times
5. **UUID Support**: Ready for UUID primary keys (currently using auto-incrementing integers)

---

## Entity Relationship Diagram

```
┌──────────────┐
│     User     │
│ (AbstractUser)│
└──────┬───────┘
       │
       │ 1:N
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────┐                      ┌──────────────┐
│   Listing    │                      │   CartItem   │
│              │                      │              │
│ - product    │◄──────────┐         │              │
│ - service    │            │         └──────┬───────┘
│ - supplier   │            │                │
└──────┬───────┘            │                │
       │                    │                │
       │ 1:N                │ N:1            │
       │                    │                │
       ▼                    │                │
┌──────────────┐            │                │
│ListingImage  │            │                │
│(GenericFK)   │            │                │
└──────────────┘            │                │
                            │                │
       ┌────────────────────┘                │
       │                                     │
       ▼                                     ▼
┌──────────────┐                      ┌──────────────┐
│    Order     │                      │   Payment    │
│              │◄─────────────────────┤              │
└──────┬───────┘                      └──────────────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│Conversation  │
│              │
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│   Message    │
│              │
└──────────────┘

┌──────────────┐
│SearchIndex   │
│Entry         │
│(GenericFK)   │
│+ embedding   │
└──────────────┘
```

---

## Core Models

### 1. User Model

**Location:** `teseapi/models.py`

Extended from Django's `AbstractUser` with marketplace-specific fields.

```python
class User(AbstractUser):
    location = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    service_type = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `username` | CharField(150) | Unique, Required | Login username |
| `email` | EmailField | Unique, Required | Email address |
| `password` | CharField(128) | Required | Hashed password |
| `first_name` | CharField(150) | Optional | First name |
| `last_name` | CharField(150) | Optional | Last name |
| `is_active` | Boolean | Default: True | Account active status |
| `is_staff` | Boolean | Default: False | Staff status |
| `is_superuser` | Boolean | Default: False | Superuser status |
| `date_joined` | DateTime | Auto | Registration date |
| `last_login` | DateTime | Auto | Last login time |
| `location` | CharField(255) | Required | User location |
| `bio` | TextField | Optional | User biography |
| `business_name` | CharField(255) | Optional | Business/farm name |
| `service_type` | CharField(255) | Optional | Type of service provided |
| `phone_number` | CharField(20) | Unique, Optional | Phone number |

**Indexes:**
- Primary key: `id`
- Unique: `username`, `email`, `phone_number`

**Related Models:**
- `listings` (One-to-Many → Listing)
- `cart_items` (One-to-Many → CartItem)
- `orders` (One-to-Many → Order)
- `sent_messages` (One-to-Many → Message)

---

### 2. Listing Model

**Location:** `teseapi/models.py`

Unified model for all listing types (products, services, supplier products).

```python
class Listing(models.Model):
    LISTING_TYPES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('supplier_product', 'Supplier Product'),
    ]
    
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
    
    # Type-specific fields (nullable)
    category = models.CharField(max_length=100, blank=True, null=True)
    organic = models.BooleanField(default=False, blank=True, null=True)
    provider = models.CharField(max_length=255, blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    
    # Generic relations
    images = GenericRelation('ListingImage')
    cart_items = GenericRelation('CartItem')
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `listing_type` | CharField(20) | Choices, Required | Type: product/service/supplier_product |
| `user` | ForeignKey | Required, CASCADE | Listing owner |
| `name` | CharField(255) | Required | Listing title |
| `location` | CharField(255) | Required | Location |
| `price` | Decimal(10,2) | Required, Min: 0.01 | Price |
| `unit` | CharField(50) | Required | Unit of measurement |
| `description` | TextField | Required | Detailed description |
| `status` | CharField(20) | Default: 'active' | Status (active/inactive/sold) |
| `category` | CharField(100) | Optional | Category/classification |
| `organic` | Boolean | Optional | Organic certification (products) |
| `provider` | CharField(255) | Optional | Service provider name |
| `supplier` | CharField(255) | Optional | Supplier name |
| `created_at` | DateTime | Auto-add | Creation timestamp |
| `updated_at` | DateTime | Auto | Last update timestamp |

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id`
- Index: `created_at` (for sorting)
- Index: `status` (for filtering)
- Composite: `(listing_type, status)`

**Related Models:**
- `user` (Many-to-One → User)
- `images` (One-to-Many → ListingImage via GenericForeignKey)
- `cart_items` (One-to-Many → CartItem via GenericForeignKey)

**Business Logic:**
```python
def to_search_document(self):
    """Convert listing to searchable document"""
    # Used by search indexing system
    
def is_available(self):
    """Check if listing is available for purchase"""
    return self.status == 'active'
```

---

### 3. ListingImage Model

**Location:** `teseapi/models.py`

Stores CDN URLs for listing images using Generic Foreign Keys.

```python
class ListingImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    image_url = models.URLField(max_length=500, default="...")
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `content_type` | ForeignKey | Required, CASCADE | ContentType reference |
| `object_id` | UUID | Required | Related object ID |
| `content_object` | GenericFK | Computed | Generic relation to listing |
| `image_url` | URLField(500) | Required | Bytescale CDN URL |
| `uploaded_at` | DateTime | Auto-add | Upload timestamp |

**Indexes:**
- Primary key: `id`
- Composite: `(content_type, object_id)`

**Generic Relation:**
Can be attached to any model, currently used for:
- Listing (products, services, supplier products)

---

### 4. Category Model

**Location:** `teseapi/models.py`

Product/service categorization (currently simple, can be hierarchical).

```python
class Category(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `name` | CharField(250) | Required | Category name |
| `description` | CharField(250) | Required | Category description |

**Future Enhancement:**
```python
# Hierarchical categories
parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
slug = models.SlugField(unique=True)
```

---

### 5. Location Model

**Location:** `teseapi/models.py`

Geographical location reference data.

```python
class Location(models.Model):
    region = models.CharField(max_length=250)
    district = models.CharField(max_length=250)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `region` | CharField(250) | Required | Region name |
| `district` | CharField(250) | Required | District name |

---

### 6. CartItem Model

**Location:** `teseapi/models.py`

Shopping cart items for users.

```python
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `user` | ForeignKey | Required, CASCADE | Cart owner |
| `listing` | ForeignKey | Required, CASCADE | Listing being purchased |
| `quantity` | PositiveInteger | Default: 1 | Quantity |
| `price` | Decimal(10,2) | Required | Price snapshot |
| `created_at` | DateTime | Auto-add | Added to cart timestamp |

**Indexes:**
- Primary key: `id`
- Foreign keys: `user_id`, `listing_id`
- Unique together: `(user, listing)` (prevents duplicates)

**Computed Fields:**
```python
@property
def subtotal(self):
    return self.quantity * self.price
```

---

### 7. Order Model

**Location:** `teseapi/models.py`

Customer orders and order tracking.

```python
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default="stripe")
    shipping_info = models.JSONField(null=True, blank=True)
    items = models.JSONField(null=True, blank=True)
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `user` | ForeignKey | Required, CASCADE | Customer |
| `total_amount` | Decimal(10,2) | Required | Order total |
| `status` | CharField(20) | Default: "PENDING" | Order status |
| `created_at` | DateTime | Auto-add | Order creation time |
| `payment_method` | CharField(50) | Default: "stripe" | Payment gateway used |
| `shipping_info` | JSONField | Optional | Shipping details (flexible) |
| `items` | JSONField | Optional | Order items snapshot |
| `transaction_ref` | CharField(255) | Optional | External transaction ID |

**Status Values:**
- `PENDING`: Order created, payment not completed
- `PAID`: Payment successful
- `PROCESSING`: Order being prepared
- `SHIPPED`: Order shipped
- `DELIVERED`: Order delivered
- `CANCELLED`: Order cancelled
- `FAILED`: Payment failed

**Indexes:**
- Primary key: `id`
- Foreign key: `user_id`
- Index: `status`, `created_at`

---

### 8. Payment Model

**Location:** `teseapi/models.py`

Payment transactions linked to orders.

```python
class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="INITIATED")
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `order` | ForeignKey | Required, CASCADE | Associated order |
| `amount` | Decimal(10,2) | Required | Payment amount |
| `method` | CharField(50) | Required | Payment method (stripe/paynow) |
| `status` | CharField(20) | Default: "INITIATED" | Payment status |
| `transaction_ref` | CharField(255) | Optional | Gateway transaction reference |
| `created_at` | DateTime | Auto-add | Payment initiation time |

**Status Values:**
- `INITIATED`: Payment process started
- `SUCCESS`: Payment successful
- `FAILED`: Payment failed
- `REFUNDED`: Payment refunded

**Indexes:**
- Primary key: `id`
- Foreign key: `order_id`
- Index: `transaction_ref` (for webhook lookups)

---

### 9. SearchIndexEntry Model

**Location:** `search/models.py`

Vector embeddings for semantic search.

```python
from pgvector.django import VectorField

class SearchIndexEntry(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict)
    embedding = VectorField(dim=384, default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `content_type` | ForeignKey | Required, CASCADE | ContentType reference |
| `object_id` | PositiveInteger | Required | Related object ID |
| `content_object` | GenericFK | Computed | Generic relation |
| `title` | CharField(255) | Required | Searchable title |
| `description` | TextField | Optional | Searchable description |
| `metadata` | JSONField | Default: {} | Additional searchable data |
| `embedding` | VectorField(384) | Default: [] | 384-dim vector embedding |
| `created_at` | DateTime | Auto-add | Index creation time |
| `updated_at` | DateTime | Auto | Last update time |

**Indexes:**
- Primary key: `id`
- Unique together: `(content_type, object_id)`
- **Vector index**: `embedding` (for similarity search)

**PostgreSQL Extensions Required:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 10. Message Models

**Location:** `modules/messaging/models.py`

Real-time messaging between users.

```python
class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
```

**Conversation Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `participants` | ManyToMany | Required | Conversation participants |
| `created_at` | DateTime | Auto-add | Conversation start time |
| `updated_at` | DateTime | Auto | Last message time |

**Message Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Primary key |
| `conversation` | ForeignKey | Required, CASCADE | Parent conversation |
| `sender` | ForeignKey | Required, CASCADE | Message sender |
| `content` | TextField | Required | Message content |
| `timestamp` | DateTime | Auto-add | Message timestamp |
| `is_read` | Boolean | Default: False | Read status |

**Indexes:**
- Primary keys: `id`
- Foreign keys: `conversation_id`, `sender_id`
- Index: `timestamp` (for ordering)
- Index: `is_read` (for unread count queries)

---

## Model Relationships

### Relationship Summary

```
User (1) ←→ (N) Listing
User (1) ←→ (N) CartItem
User (1) ←→ (N) Order
User (M) ←→ (N) Conversation
User (1) ←→ (N) Message

Listing (1) ←→ (N) ListingImage (Generic)
Listing (1) ←→ (N) CartItem
Listing (1) ←→ (N) SearchIndexEntry (Generic)

Order (1) ←→ (N) Payment

Conversation (1) ←→ (N) Message
```

### Cascade Behaviors

| Parent Model | Child Model | On Delete |
|--------------|-------------|-----------|
| User | Listing | CASCADE |
| User | CartItem | CASCADE |
| User | Order | CASCADE |
| User | Message | CASCADE |
| Listing | ListingImage | CASCADE |
| Listing | CartItem | CASCADE |
| Order | Payment | CASCADE |
| Conversation | Message | CASCADE |
| ContentType | SearchIndexEntry | CASCADE |

**Reasoning:**
- **CASCADE**: When a user is deleted, all their listings, orders, etc. should also be deleted
- **PROTECT**: Could be used for Categories to prevent deletion if listings exist
- **SET_NULL**: Could be used to preserve order history even if listing is deleted

---

## Database Indexes

### Automatic Indexes
Django automatically creates indexes for:
- Primary keys
- Foreign keys
- Unique fields

### Custom Indexes

```python
class Listing(models.Model):
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'listing_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'status']),
        ]
```

### Vector Index (pgvector)

```sql
-- Created during migration
CREATE INDEX ON search_searchindexentry 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**Performance Notes:**
- Vector index: O(log n) search complexity
- Suitable for up to millions of vectors
- Tune `lists` parameter based on dataset size

---

## Migrations

### Migration Files

Migrations are stored in:
```
teseapi/migrations/
search/migrations/
modules/messaging/migrations/
```

### Key Migrations

**Initial Migration:**
```python
# 0001_initial.py
operations = [
    migrations.CreateModel('User'),
    migrations.CreateModel('Listing'),
    migrations.CreateModel('ListingImage'),
    # ...
]
```

**Adding pgvector:**
```python
# search/migrations/0001_initial.py
operations = [
    migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS vector'),
    migrations.CreateModel('SearchIndexEntry'),
]
```

### Running Migrations

```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate teseapi 0003_previous_migration
```

---

## Query Patterns

### Efficient Queries

#### 1. List Listings with User and Images
```python
# Bad: N+1 queries
listings = Listing.objects.all()
for listing in listings:
    print(listing.user.username)  # Extra query per listing
    print(listing.images.count())  # Extra query per listing

# Good: Optimized query
listings = Listing.objects.select_related('user').prefetch_related('images').all()
```

#### 2. Filter Active Listings
```python
active_listings = Listing.objects.filter(
    status='active'
).select_related('user').order_by('-created_at')
```

#### 3. Get User's Cart with Listings
```python
cart_items = CartItem.objects.filter(
    user=request.user
).select_related('listing', 'listing__user').prefetch_related('listing__images')
```

#### 4. Vector Similarity Search
```python
from django.contrib.postgres.search import SearchVector

# Generate embedding for query
query_embedding = generate_embedding("fresh vegetables")

# Find similar entries
results = SearchIndexEntry.objects.order_by(
    embedding.cosine_distance(query_embedding)
)[:10]
```

#### 5. Aggregate Queries
```python
from django.db.models import Count, Sum, Avg

# Total sales per user
user_sales = Order.objects.filter(
    status='PAID'
).values('user__username').annotate(
    total_sales=Sum('total_amount'),
    order_count=Count('id')
)

# Average listing price by category
category_prices = Listing.objects.values('category').annotate(
    avg_price=Avg('price'),
    count=Count('id')
)
```

### Raw SQL Queries

When ORM is insufficient:
```python
from django.db import connection

def complex_analytics_query():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                l.category,
                COUNT(*) as listing_count,
                AVG(o.total_amount) as avg_order_value
            FROM teseapi_listing l
            LEFT JOIN teseapi_cartitem ci ON ci.listing_id = l.id
            LEFT JOIN teseapi_order o ON o.user_id = ci.user_id
            WHERE l.status = 'active'
            GROUP BY l.category
            ORDER BY listing_count DESC
        """)
        return cursor.fetchall()
```

---

## Database Maintenance

### Backup Strategy

```bash
# PostgreSQL backup
pg_dump -h hostname -U username dbname > backup.sql

# Restore
psql -h hostname -U username dbname < backup.sql
```

### Vacuum and Analyze

```sql
-- Reclaim storage and update statistics
VACUUM ANALYZE;

-- For specific table
VACUUM ANALYZE teseapi_listing;
```

### Index Maintenance

```sql
-- Rebuild indexes
REINDEX TABLE teseapi_listing;

-- Check index usage
SELECT * FROM pg_stat_user_indexes 
WHERE schemaname = 'public';
```

---

## Performance Considerations

### Query Optimization
1. Always use `select_related()` for ForeignKey
2. Always use `prefetch_related()` for reverse ForeignKey and ManyToMany
3. Use `only()` and `defer()` to limit fields
4. Add database indexes for frequently filtered/sorted fields
5. Use `exists()` instead of `count()` for existence checks

### Caching Strategy
```python
from django.core.cache import cache

def get_popular_listings():
    cache_key = 'popular_listings'
    listings = cache.get(cache_key)
    
    if not listings:
        listings = Listing.objects.filter(
            status='active'
        ).select_related('user').prefetch_related('images')[:20]
        
        cache.set(cache_key, listings, 300)  # 5 minutes
    
    return listings
```

### Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection reuse
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

---

*Last Updated: 2024*
*Schema Version: 1.0.0*
