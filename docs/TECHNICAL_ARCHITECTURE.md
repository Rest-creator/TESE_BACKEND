# TESE Marketplace - Technical Architecture

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Design Patterns](#design-patterns)
3. [Layer Architecture](#layer-architecture)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Scalability & Performance](#scalability--performance)
8. [Technology Decisions](#technology-decisions)

---

## Architecture Overview

### High-Level Architecture

TESE Marketplace follows a **layered, modular architecture** based on Domain-Driven Design (DDD) principles combined with Django's MTV (Model-Template-View) pattern adapted for API development.

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│         (Web Frontend, Mobile Apps, Third-party APIs)        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS + WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│            (Django URLs, CORS, Authentication)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│        (Views, Serializers, ViewSets, Consumers)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│              (Services, Use Cases, Validators)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│              (Repositories, QuerySets, Managers)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│         (PostgreSQL/SQLite, Redis, Bytescale CDN)           │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Modularity**: Features organized into independent modules
3. **Dependency Inversion**: High-level modules don't depend on low-level modules
4. **Single Responsibility**: Each component has one reason to change
5. **Open/Closed**: Open for extension, closed for modification

---

## Design Patterns

### 1. **Repository Pattern**

Abstracts data access logic, providing a collection-like interface for domain objects.

```python
# modules/listings/repository/listing_repository.py
class ListingRepository:
    """Repository for Listing entities"""
    
    @staticmethod
    def get_all_listings():
        """Retrieve all listings"""
        return Listing.objects.all()
    
    @staticmethod
    def get_listing_by_id(listing_id):
        """Retrieve a specific listing by ID"""
        return Listing.objects.get(id=listing_id)
    
    @staticmethod
    def create_listing(data):
        """Create a new listing"""
        return Listing.objects.create(**data)
    
    @staticmethod
    def filter_by_status(status):
        """Filter listings by status"""
        return Listing.objects.filter(status=status)
```

**Benefits:**
- Centralizes data access logic
- Makes testing easier with mock repositories
- Reduces coupling between business logic and ORM

### 2. **Service Layer Pattern**

Encapsulates business logic separate from data access and presentation.

```python
# modules/listings/service/listing_service.py
class ListingService:
    """Service layer for listing business logic"""
    
    @staticmethod
    def create_listing(user, data):
        """Business logic for creating a listing"""
        # Validation
        if not data.get('price') or data['price'] <= 0:
            raise ValueError("Price must be positive")
        
        # Business rules
        data['user'] = user
        data['status'] = 'active'
        
        # Repository call
        listing = ListingRepository.create_listing(data)
        
        # Post-creation tasks
        index_object(listing)  # Search indexing
        
        return listing
```

**Benefits:**
- Keeps business logic separate from views
- Reusable across different interfaces (API, WebSocket, CLI)
- Easier to test and maintain

### 3. **Entity Pattern**

Domain objects that encapsulate data and behavior.

```python
# modules/listings/entities/listing_entity.py
class ListingEntity:
    """Entity representing a marketplace listing"""
    
    def __init__(self, id, name, price, user, **kwargs):
        self.id = id
        self.name = name
        self.price = price
        self.user = user
        self.metadata = kwargs
    
    def is_active(self):
        """Check if listing is active"""
        return self.metadata.get('status') == 'active'
    
    def calculate_total(self, quantity):
        """Calculate total price for quantity"""
        return self.price * quantity
```

**Benefits:**
- Encapsulates domain logic
- Self-contained validation
- Easier to reason about business rules

### 4. **Gateway Pattern**

Provides abstraction for external services (payments, CDN, etc.).

```python
# modules/payment_module/gateways/stripe_gateway.py
class StripeGateway:
    """Gateway for Stripe payment processing"""
    
    def create_payment_intent(self, amount, currency="usd"):
        """Create a Stripe payment intent"""
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        return stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency
        )
```

**Benefits:**
- Isolates external dependencies
- Easy to swap implementations
- Simplifies testing with mock gateways

### 5. **Observer Pattern (Signals)**

Django signals for decoupled event handling.

```python
# search/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from teseapi.models import Listing
from .services.search_services import index_object, delete_object_from_index

@receiver(post_save, sender=Listing)
def index_listing_on_save(sender, instance, created, **kwargs):
    """Automatically index listing when saved"""
    index_object(instance)

@receiver(post_delete, sender=Listing)
def remove_listing_from_index(sender, instance, **kwargs):
    """Remove listing from search index when deleted"""
    delete_object_from_index(instance)
```

**Benefits:**
- Loose coupling between components
- Automatic event handling
- Easy to add new behaviors

---

## Layer Architecture

### 1. **Presentation Layer**

**Responsibilities:**
- HTTP request/response handling
- Input validation and serialization
- Authentication and authorization
- WebSocket connections

**Components:**
```
teseapi/views_app/
├── auth_views.py          # Authentication endpoints
├── listing_views.py       # Listing CRUD operations
├── service_views.py       # Service-specific views
├── supplier_views.py      # Supplier-specific views
└── user_listings_view.py  # User listing management
```

**Example:**
```python
# teseapi/views_app/listing_views.py
class ListingListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all listings"""
        listings = ListingService.get_all_active_listings()
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new listing"""
        serializer = ListingSerializer(data=request.data)
        if serializer.is_valid():
            listing = ListingService.create_listing(
                request.user, 
                serializer.validated_data
            )
            return Response(
                ListingSerializer(listing).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 2. **Business Logic Layer**

**Responsibilities:**
- Business rules enforcement
- Workflow orchestration
- Domain logic
- Cross-cutting concerns

**Components:**
```
modules/*/services/
├── auth_service.py        # Authentication logic
├── listing_service.py     # Listing business logic
├── messaging_service.py   # Messaging logic
└── payment_services.py    # Payment processing logic
```

**Example:**
```python
# modules/payment_module/services/payment_services.py
class PaymentService:
    @staticmethod
    def process_payment(order, payment_method):
        """Process payment for an order"""
        # Select gateway based on payment method
        if payment_method == 'stripe':
            gateway = StripeGateway()
        elif payment_method == 'paynow':
            gateway = PayNowGateway()
        else:
            raise ValueError("Invalid payment method")
        
        # Create payment intent
        intent = gateway.create_payment_intent(
            order.total_amount
        )
        
        # Create payment record
        payment = PaymentRepository.create_payment({
            'order': order,
            'amount': order.total_amount,
            'method': payment_method,
            'transaction_ref': intent['id'],
            'status': 'INITIATED'
        })
        
        return payment, intent
```

### 3. **Data Access Layer**

**Responsibilities:**
- Database queries
- ORM abstraction
- Query optimization
- Data persistence

**Components:**
```
modules/*/repositories/
├── user_repository.py        # User data access
├── listing_repository.py     # Listing data access
├── messaging_repository.py   # Message data access
└── payment_repository.py     # Payment data access
```

**Example:**
```python
# modules/listings/repository/listing_repository.py
class ListingRepository:
    @staticmethod
    def get_active_listings():
        """Get all active listings with optimized query"""
        return Listing.objects.filter(
            status='active'
        ).select_related(
            'user'
        ).prefetch_related(
            'images'
        ).order_by('-created_at')
    
    @staticmethod
    def get_user_listings(user_id):
        """Get all listings for a specific user"""
        return Listing.objects.filter(
            user_id=user_id
        ).prefetch_related('images')
```

### 4. **Domain Layer**

**Responsibilities:**
- Domain models (Django ORM models)
- Business entities
- Value objects
- Domain events

**Components:**
```
teseapi/models.py           # Core domain models
modules/*/entities/         # Domain entities
modules/*/Implementation/   # Model implementations
```

---

## Core Components

### 1. **Authentication System**

**Architecture:**
```
Client Request
    ↓
JWT Token Validation (JWTAuthentication)
    ↓
User Retrieval (AUTH_USER_MODEL)
    ↓
Permission Check (IsAuthenticated)
    ↓
View Processing
```

**Token Flow:**
```
1. User Login (POST /api/signin/)
   → Validate credentials
   → Generate access + refresh tokens
   → Return tokens

2. API Request with Token
   → Extract Bearer token from header
   → Validate token signature and expiry
   → Load user from token payload
   → Process request

3. Token Refresh (POST /api/auth/token/refresh/)
   → Validate refresh token
   → Generate new access token
   → Blacklist old refresh token (if rotation enabled)
   → Return new tokens
```

**Configuration:**
```python
# teseapp/settings.py
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ALGORITHM": "HS256",
}
```

### 2. **Search System**

**Architecture:**
```
User Query
    ↓
Search Service (search_by_vector)
    ↓
Embedding Generation (SentenceTransformer)
    ↓
Vector Similarity Search (pgvector)
    ↓
Results Ranking & Filtering
    ↓
Serialized Response
```

**Indexing Pipeline:**
```
1. Model Save Signal
   ↓
2. Extract Search Document (to_search_document)
   ↓
3. Generate Embedding (384-dim vector)
   ↓
4. Store in SearchIndexEntry
   ↓
5. Vector Index Update
```

**Technology Stack:**
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Dimension**: 384
- **Database Extension**: pgvector
- **Similarity Metric**: Cosine similarity

### 3. **Payment Processing**

**Multi-Gateway Architecture:**
```
Payment Request
    ↓
PaymentService.process_payment()
    ↓
Gateway Selection (Stripe/PayNow)
    ↓
Gateway-Specific Processing
    ↓
Payment Record Creation
    ↓
Order Status Update
    ↓
Webhook Handling (async)
```

**Supported Gateways:**
- **Stripe**: International payments (cards, wallets)
- **PayNow**: Local payments (Zimbabwe - mobile money)

**Payment States:**
```
INITIATED → SUCCESS → Order.PAID
          ↘ FAILED  → Order.FAILED
```

### 4. **Real-time Messaging**

**WebSocket Architecture:**
```
Client WebSocket Connection
    ↓
Channels ASGI Application
    ↓
Consumer Routing
    ↓
Redis Channel Layer
    ↓
Message Broadcasting
    ↓
Connected Clients
```

**Message Flow:**
```
1. User A sends message
   ↓
2. Consumer receives message
   ↓
3. Save to database (Message model)
   ↓
4. Broadcast to channel group
   ↓
5. User B receives message in real-time
```

**Technology:**
- **Protocol**: WebSocket
- **Framework**: Django Channels 4.2.2
- **Message Broker**: Redis
- **Backend**: channels_redis

### 5. **Image Management**

**CDN Architecture:**
```
Image Upload Request
    ↓
ImageService.upload_image()
    ↓
Bytescale API Upload
    ↓
CDN URL Received
    ↓
ListingImage.create(image_url)
    ↓
Return CDN URL to Client
```

**Features:**
- Offloaded storage to Bytescale CDN
- Automatic optimization and resizing
- Fast global delivery
- No local storage required

---

## Data Flow

### 1. **Listing Creation Flow**

```
[Client] POST /api/listings/
    ↓
[View] ListingListCreateView.post()
    ↓ Validate request data
[Serializer] ListingSerializer.is_valid()
    ↓ Deserialize and validate
[Service] ListingService.create_listing()
    ↓ Apply business rules
[Repository] ListingRepository.create_listing()
    ↓ Persist to database
[ORM] Listing.objects.create()
    ↓ Trigger signals
[Signal] post_save → index_listing_on_save()
    ↓
[Search] index_object()
    ↓ Generate embedding
[Search] SearchIndexEntry.create()
    ↓
[View] Return serialized listing
    ↓
[Client] Receive 201 Created response
```

### 2. **Search Flow**

```
[Client] GET /api/search/?q=fresh vegetables
    ↓
[View] SearchView.get()
    ↓ Extract query
[Service] search_by_vector("fresh vegetables")
    ↓ Generate query embedding
[Embedding] SentenceTransformer.encode()
    ↓ Perform similarity search
[Database] SELECT * FROM search_index 
           ORDER BY embedding <=> query_vector
           LIMIT 10
    ↓ Fetch related objects
[Repository] Retrieve Listing objects
    ↓ Serialize results
[Serializer] SearchResultSerializer
    ↓
[Client] Receive search results
```

### 3. **Payment Flow**

```
[Client] POST /api/checkout/
    ↓ Cart items + shipping info
[View] CheckoutViewSet.create()
    ↓ Validate cart
[Service] OrderService.create_order()
    ↓ Calculate total
[Repository] Order.create()
    ↓ Process payment
[Service] PaymentService.process_payment()
    ↓ Select gateway
[Gateway] StripeGateway.create_payment_intent()
    ↓ External API call
[Stripe API] Create PaymentIntent
    ↓ Return client_secret
[View] Return payment details
    ↓
[Client] Complete payment with Stripe.js
    ↓ Stripe webhook
[Webhook] POST /api/webhooks/stripe/
    ↓ Verify signature
[Service] PaymentService.handle_webhook()
    ↓ Update payment status
[Repository] Payment.update(status='SUCCESS')
    ↓ Update order
[Repository] Order.update(status='PAID')
    ↓ Send confirmation
[Notification] Email/SMS to user
```

---

## Security Architecture

### 1. **Authentication & Authorization**

**Layers:**
1. **Network Layer**: HTTPS/TLS encryption
2. **Application Layer**: JWT token validation
3. **Permission Layer**: Django REST Framework permissions
4. **Object Layer**: Custom object-level permissions

**Token Security:**
- HS256 algorithm with secret key
- Short-lived access tokens (30 minutes)
- Refresh token rotation
- Token blacklisting on logout
- No session state required

### 2. **Input Validation**

**Validation Layers:**
```
Request Data
    ↓
[Serializer] Field-level validation
    ↓
[Serializer] Custom validate_<field> methods
    ↓
[Serializer] Object-level validate() method
    ↓
[Service] Business rule validation
    ↓
[Repository] Database constraints
```

### 3. **CORS Configuration**

```python
CORS_ALLOWED_ORIGINS = [
    "https://tese-dvx.pages.dev",      # Production frontend
    "https://swapback.zchpc.ac.zw",    # Alternative domain
    "http://localhost:8080",            # Development
]
CORS_ALLOW_CREDENTIALS = False         # JWT is stateless
```

### 4. **Environment Variables**

Sensitive data stored in environment variables:
- `DJANGO_SECRET_KEY`: Django secret key
- `STRIPE_SECRET_KEY`: Stripe API key
- `PAYNOW_INTEGRATION_ID`: PayNow integration ID
- `PAYNOW_SECRET_KEY`: PayNow secret key
- `BYTESCALE_API_KEY`: Bytescale API key

### 5. **Database Security**

- Parameterized queries (ORM prevents SQL injection)
- Connection pooling
- SSL/TLS for database connections in production
- Regular backups
- Encrypted sensitive fields (future enhancement)

---

## Scalability & Performance

### 1. **Database Optimization**

**Query Optimization:**
```python
# Bad: N+1 query problem
listings = Listing.objects.all()
for listing in listings:
    print(listing.user.username)  # Query per listing

# Good: select_related for foreign keys
listings = Listing.objects.select_related('user').all()

# Good: prefetch_related for reverse relations
listings = Listing.objects.prefetch_related('images').all()
```

**Indexing Strategy:**
- Primary keys (automatic)
- Foreign keys (automatic)
- Frequently queried fields (status, created_at, user_id)
- Vector index for embeddings (pgvector)

### 2. **Caching Strategy**

**Levels:**
1. **Database Query Cache**: Django ORM cache
2. **Redis Cache**: Session data, channel layer
3. **CDN Cache**: Static files, images (Bytescale)

**Future Enhancements:**
```python
# Cache frequently accessed data
from django.core.cache import cache

def get_active_listings():
    cache_key = 'active_listings'
    listings = cache.get(cache_key)
    
    if listings is None:
        listings = Listing.objects.filter(status='active')
        cache.set(cache_key, listings, 300)  # 5 minutes
    
    return listings
```

### 3. **Load Balancing**

**Horizontal Scaling:**
- Stateless API (JWT, no sessions)
- Multiple gunicorn workers
- Load balancer support ready
- Database connection pooling

**Configuration:**
```
# Procfile
web: gunicorn teseapp.wsgi:application 
     --bind 0.0.0.0:$PORT 
     --workers 3
     --timeout 120
```

### 4. **Asynchronous Processing**

**Current:**
- WebSocket connections (async)
- Channels for real-time features

**Future:**
- Celery for background tasks
- Async payment webhook processing
- Batch search indexing
- Email notifications

### 5. **CDN Integration**

**Benefits:**
- Reduced server load
- Faster image delivery
- Global distribution
- Automatic optimization

---

## Technology Decisions

### 1. **Django Framework**

**Why Django?**
- ✅ Mature, battle-tested framework
- ✅ Built-in admin interface
- ✅ Excellent ORM
- ✅ Large ecosystem
- ✅ Security features built-in
- ✅ Rapid development

**Alternatives Considered:**
- FastAPI: Async-first, but less mature ecosystem
- Flask: Too minimal for complex project
- Express.js: Different language ecosystem

### 2. **PostgreSQL vs SQLite**

**Development: SQLite**
- Fast setup
- No external dependencies
- File-based database

**Production: PostgreSQL**
- ACID compliance
- Advanced features (JSON, arrays, pgvector)
- Better concurrency
- Production-ready

### 3. **JWT Authentication**

**Why JWT?**
- ✅ Stateless (no session storage)
- ✅ Scalable (no shared session store)
- ✅ Mobile-friendly
- ✅ API-first design

**Alternatives:**
- Session-based: Requires sticky sessions
- OAuth2: Overkill for current needs

### 4. **Semantic Search**

**Why Vector Search?**
- ✅ Better relevance than keyword search
- ✅ Understands context
- ✅ Language flexibility
- ✅ Future-proof (AI/ML trend)

**Technology Choice:**
- pgvector: Native PostgreSQL extension
- SentenceTransformers: State-of-the-art embeddings
- Fallback to SQLite text search in development

### 5. **Channels for WebSocket**

**Why Channels?**
- ✅ Django-native solution
- ✅ Same codebase as REST API
- ✅ Redis-backed scalability
- ✅ Easy to learn for Django developers

**Alternatives:**
- Socket.IO: Requires separate Node.js server
- Native WebSocket: Lower-level, more complex

---

## Monitoring & Observability

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# In services
def create_listing(user, data):
    logger.info(f"Creating listing for user {user.id}")
    try:
        listing = ListingRepository.create_listing(data)
        logger.info(f"Listing {listing.id} created successfully")
        return listing
    except Exception as e:
        logger.error(f"Failed to create listing: {str(e)}")
        raise
```

### Error Tracking
- Django error emails (DEBUG=False)
- Custom exception handlers
- Structured logging

### Performance Monitoring
- Django Debug Toolbar (development)
- Query count monitoring
- Response time tracking

---

## Deployment Architecture

```
                      [Load Balancer]
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
          [App Server 1]          [App Server 2]
          (Gunicorn)              (Gunicorn)
                │                       │
                └───────────┬───────────┘
                            ▼
                    [PostgreSQL]
                            │
                            ▼
                       [Redis]
                            │
                            ▼
                    [Bytescale CDN]
```

**Components:**
- **App Servers**: Multiple gunicorn workers
- **Database**: PostgreSQL with pgvector
- **Cache/Queue**: Redis
- **Storage**: Bytescale CDN
- **Reverse Proxy**: Nginx (optional)

---

*Last Updated: 2024*
*Version: 1.0.0*
