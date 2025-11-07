# TESE Marketplace - Module Documentation

## Table of Contents
1. [Module Overview](#module-overview)
2. [Authentication Module](#authentication-module)
3. [Listings Module](#listings-module)
4. [Messaging Module](#messaging-module)
5. [Payment Module](#payment-module)
6. [Search Module](#search-module)
7. [Utils Module](#utils-module)

---

## Module Overview

TESE Marketplace follows a modular architecture where each feature is organized into self-contained modules following Clean Architecture principles.

### Module Structure

Each module typically contains:
```
module_name/
├── entities/          # Domain entities (business objects)
├── repositories/      # Data access layer
├── serializers/       # API serializers
├── services/          # Business logic
└── implementation/    # Django-specific implementations
```

---

## Authentication Module

**Location:** `modules/auth/`

### Purpose
Handles user authentication, registration, and JWT token management.

### Components

#### 1. **User Entity** (`entities/user_entity.py`)

Domain representation of a user.

```python
class UserEntity:
    def __init__(self, id, username, email, location, **kwargs):
        self.id = id
        self.username = username
        self.email = email
        self.location = location
        self.business_name = kwargs.get('business_name')
        self.service_type = kwargs.get('service_type')
        self.phone_number = kwargs.get('phone_number')
    
    @classmethod
    def from_model(cls, user_model):
        """Convert Django User model to entity"""
        return cls(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            location=user_model.location,
            business_name=user_model.business_name,
            service_type=user_model.service_type,
            phone_number=user_model.phone_number
        )
```

#### 2. **User Repository** (`repositories/user_repository.py`)

Data access for user operations.

```python
class UserRepository:
    @staticmethod
    def create_user(data):
        """Create a new user"""
        user = User.objects.create_user(
            username=data['username'],
            email=data.get('email'),
            password=data['password'],
            location=data['location'],
            # ... other fields
        )
        return user
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.objects.filter(email=email).first()
    
    @staticmethod
    def find_by_phone(phone):
        """Find user by phone number"""
        return User.objects.filter(phone_number=phone).first()
```

#### 3. **Auth Service** (`services/auth_service.py`)

Business logic for authentication.

```python
class AuthService:
    @staticmethod
    def signup(data):
        """Register new user and return tokens"""
        # Validate email/phone uniqueness
        # Create user via repository
        # Generate JWT tokens
        # Return user entity + tokens
    
    @staticmethod
    def signin(identifier, password):
        """Authenticate user and return tokens"""
        # Support email, phone, or username login
        # Verify credentials
        # Generate JWT tokens
        # Return user entity + tokens
```

### API Integration

**Views:** `teseapi/views_app/auth_views.py`

```python
class SignupView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            result = AuthService.signup(serializer.validated_data)
            return Response(result, status=201)
        return Response(serializer.errors, status=400)
```

---

## Listings Module

**Location:** `modules/listings/`

### Purpose
Manages all types of listings (products, services, supplier products) with image handling.

### Components

#### 1. **Listing Entity** (`entities/listing_entity.py`)

Domain model for listings.

```python
class ListingEntity:
    def __init__(self, id, name, price, unit, listing_type, **kwargs):
        self.id = id
        self.name = name
        self.price = price
        self.unit = unit
        self.listing_type = listing_type
        self.description = kwargs.get('description')
        self.location = kwargs.get('location')
        self.status = kwargs.get('status', 'active')
```

#### 2. **Listing Repository** (`repository/listing_repository.py`)

```python
class ListingRepository:
    @staticmethod
    def get_all_active_listings():
        """Get all active listings with related data"""
        return Listing.objects.filter(
            status='active'
        ).select_related('user').prefetch_related('images')
    
    @staticmethod
    def create_listing(data):
        """Create a new listing"""
        return Listing.objects.create(**data)
    
    @staticmethod
    def get_by_user(user_id):
        """Get listings by user"""
        return Listing.objects.filter(user_id=user_id)
```

#### 3. **Image Repository** (`repository/image_repository.py`)

```python
class ImageRepository:
    @staticmethod
    def create_images(listing, image_urls):
        """Create multiple images for a listing"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(listing)
        images = [
            ListingImage(
                content_type=content_type,
                object_id=listing.id,
                image_url=url
            )
            for url in image_urls
        ]
        return ListingImage.objects.bulk_create(images)
```

#### 4. **Listing Service** (`service/listing_service.py`)

```python
class ListingService:
    @staticmethod
    def create_listing(user, data):
        """Create listing with business logic"""
        # Validate price
        if data['price'] <= 0:
            raise ValueError("Price must be positive")
        
        # Set user and default status
        data['user'] = user
        data['status'] = 'active'
        
        # Extract image URLs
        image_urls = data.pop('image_urls', [])
        
        # Create listing
        listing = ListingRepository.create_listing(data)
        
        # Create images
        if image_urls:
            ImageRepository.create_images(listing, image_urls)
        
        # Index for search
        from search.services.search_services import index_object
        index_object(listing)
        
        return listing
```

### Serializers

**Location:** `modules/listings/serializer/`

```python
class ListingSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    user = UserBasicSerializer(read_only=True)
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Listing
        fields = '__all__'
```

---

## Messaging Module

**Location:** `modules/messaging/`

### Purpose
Real-time messaging between users with WebSocket support.

### Components

#### 1. **Messaging Entity** (`entities/messaging.py`)

```python
class ConversationEntity:
    def __init__(self, id, participants, created_at):
        self.id = id
        self.participants = participants
        self.created_at = created_at

class MessageEntity:
    def __init__(self, id, sender, content, timestamp):
        self.id = id
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.is_read = False
```

#### 2. **Messaging Repository** (`repositories/messaging_repository.py`)

```python
class MessagingRepository:
    @staticmethod
    def get_user_conversations(user):
        """Get all conversations for a user"""
        return Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants')
    
    @staticmethod
    def create_message(conversation, sender, content):
        """Create a new message"""
        return Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )
```

#### 3. **Messaging Service** (`services/messaging_service.py`)

```python
class MessagingService:
    @staticmethod
    def send_message(conversation_id, sender, content):
        """Send a message and notify via WebSocket"""
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Create message
        message = MessagingRepository.create_message(
            conversation, sender, content
        )
        
        # Broadcast via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conversation_{conversation_id}",
            {
                "type": "chat_message",
                "message": MessageSerializer(message).data
            }
        )
        
        return message
```

### WebSocket Integration

**Consumer:** `teseapi/consumers.py`

```python
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'conversation_{self.conversation_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Handle incoming message
```

---

## Payment Module

**Location:** `modules/payment_module/`

### Purpose
Multi-gateway payment processing (Stripe, PayNow).

### Components

#### 1. **Payment Entity** (`entities/payment_entity.py`)

```python
class PaymentEntity:
    def __init__(self, id, order_id, amount, method, status):
        self.id = id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.status = status
        self.transaction_ref = None
```

#### 2. **Payment Gateways**

**Stripe Gateway** (`gateways/stripe_gateway.py`)

```python
class StripeGateway:
    def __init__(self):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, amount, currency="usd"):
        """Create Stripe payment intent"""
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency
        )
        return {
            'id': intent.id,
            'client_secret': intent.client_secret,
            'status': intent.status
        }
    
    def verify_webhook(self, payload, signature):
        """Verify Stripe webhook signature"""
        import stripe
        return stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
```

**PayNow Gateway** (`gateways/paynow_gateway.py`)

```python
class PayNowGateway:
    def __init__(self):
        from paynow import Paynow
        self.paynow = Paynow(
            settings.PAYNOW_INTEGRATION_ID,
            settings.PAYNOW_SECRET_KEY,
            settings.PAYNOW_RETURN_URL,
            settings.PAYNOW_RESULT_URL
        )
    
    def create_payment(self, amount, email, reference):
        """Create PayNow payment"""
        payment = self.paynow.create_payment(reference, email)
        payment.add('Order', amount)
        response = self.paynow.send_mobile(payment, phone, method)
        return response
```

#### 3. **Payment Service** (`services/payment_services.py`)

```python
class PaymentService:
    @staticmethod
    def process_payment(order, payment_method):
        """Process payment using selected gateway"""
        # Select gateway
        if payment_method == 'stripe':
            gateway = StripeGateway()
            intent = gateway.create_payment_intent(order.total_amount)
        elif payment_method == 'paynow':
            gateway = PayNowGateway()
            intent = gateway.create_payment(
                order.total_amount,
                order.user.email,
                f"ORDER-{order.id}"
            )
        else:
            raise ValueError("Invalid payment method")
        
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

#### 4. **Checkout ViewSet** (`implementation/payment_views.py`)

```python
class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Process checkout"""
        # Get cart items
        cart_items = CartItem.objects.filter(user=request.user)
        
        # Create order
        order = OrderService.create_order(
            request.user,
            cart_items,
            request.data.get('shipping_info')
        )
        
        # Process payment
        payment, intent = PaymentService.process_payment(
            order,
            request.data.get('payment_method', 'stripe')
        )
        
        # Clear cart
        cart_items.delete()
        
        return Response({
            'order': OrderSerializer(order).data,
            'payment': PaymentSerializer(payment).data,
            'client_secret': intent.get('client_secret')
        }, status=201)
```

---

## Search Module

**Location:** `search/`

### Purpose
AI-powered semantic search using vector embeddings.

### Components

#### 1. **Embedding Generation** (`embeddings.py`)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text):
    """Generate 384-dim vector embedding"""
    return model.encode(text).tolist()
```

#### 2. **Search Service** (`services/search_services.py`)

```python
class SearchService:
    @staticmethod
    def index_object(instance):
        """Index an object for search"""
        from django.contrib.contenttypes.models import ContentType
        
        # Get search document
        doc = instance.to_search_document()
        
        # Generate embedding
        text = f"{doc['title']} {doc['description']}"
        embedding = generate_embedding(text)
        
        # Create or update index entry
        content_type = ContentType.objects.get_for_model(instance)
        SearchIndexEntry.objects.update_or_create(
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'title': doc['title'],
                'description': doc['description'],
                'metadata': doc['metadata'],
                'embedding': embedding
            }
        )
    
    @staticmethod
    def search_by_vector(query, filters=None, limit=10):
        """Perform semantic search"""
        # Generate query embedding
        query_embedding = generate_embedding(query)
        
        # Vector similarity search
        results = SearchIndexEntry.objects.order_by(
            SearchIndexEntry.embedding.cosine_distance(query_embedding)
        )
        
        # Apply metadata filters
        if filters:
            for key, value in filters.items():
                results = results.filter(**{f"metadata__{key}": value})
        
        return results[:limit]
```

#### 3. **Search View** (`search_views.py`)

```python
class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        # Extract metadata filters
        filters = {}
        for key, value in request.GET.items():
            if key.startswith('metadata__'):
                filter_key = key.replace('metadata__', '')
                filters[filter_key] = value
        
        # Perform search
        results = SearchService.search_by_vector(query, filters)
        
        # Serialize results
        serializer = SearchResultSerializer(results, many=True)
        
        return Response({
            'query': query,
            'results': serializer.data,
            'total': results.count()
        })
```

---

## Utils Module

**Location:** `modules/utils/`

### Purpose
Shared utilities and helper functions.

### Common Utilities

```python
# Date/Time utilities
def format_datetime(dt):
    """Format datetime for API response"""
    return dt.isoformat() if dt else None

# Validation utilities
def validate_phone_number(phone):
    """Validate international phone format"""
    import re
    return re.match(r'^\+[1-9]\d{6,14}$', phone) is not None

# Pagination utilities
def paginate_queryset(queryset, page, page_size=20):
    """Paginate queryset"""
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(page)
```

---

## Module Integration

### How Modules Work Together

```python
# Example: Creating a listing and making it searchable

# 1. API receives request
# teseapi/views_app/listing_views.py
def create_listing_view(request):
    # 2. Service handles business logic
    # modules/listings/service/listing_service.py
    listing = ListingService.create_listing(user, data)
    
    # 3. Repository persists data
    # modules/listings/repository/listing_repository.py
    ListingRepository.create_listing(data)
    
    # 4. Search module indexes
    # search/services/search_services.py
    SearchService.index_object(listing)
    
    # 5. Response serialized
    # modules/listings/serializer/listing_serializers.py
    return ListingSerializer(listing).data
```

---

*Last Updated: 2024*
*Module Version: 1.0.0*
