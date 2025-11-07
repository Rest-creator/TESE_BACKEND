# TESE Marketplace - API Documentation

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Endpoints Reference](#endpoints-reference)
4. [WebSocket API](#websocket-api)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## API Overview

### Base URL
- **Production**: `https://tesebackend-4ic7p.sevalla.app/api/`
- **Development**: `http://localhost:8000/api/`

### API Version
Current version: **v1**

### Content Type
All requests and responses use JSON format:
```
Content-Type: application/json
```

### Common Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

---

## Authentication

### Authentication Methods

TESE Marketplace uses **JWT (JSON Web Tokens)** for authentication.

### Token Types
1. **Access Token**: Short-lived (30 minutes), used for API requests
2. **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

### Authentication Flow

```
1. User signs up or signs in
   ↓
2. Server returns access + refresh tokens
   ↓
3. Client stores tokens securely
   ↓
4. Client includes access token in Authorization header
   ↓
5. When access token expires, use refresh token to get new one
   ↓
6. On logout, blacklist refresh token
```

---

## Endpoints Reference

### 1. Authentication Endpoints

#### 1.1 Sign Up

Create a new user account.

**Endpoint:** `POST /api/signup/`

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "john_farmer",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "location": "Harare",
  "phone_number": "+263771234567",
  "business_name": "John's Farm",
  "service_type": "Farmer"
}
```

**Required Fields:**
- `username` (string): Unique username
- `email` (string): Valid email address
- `password` (string): Minimum 8 characters
- `password2` (string): Must match password
- `location` (string): User's location

**Optional Fields:**
- `phone_number` (string): Phone number (unique if provided)
- `business_name` (string): Business or farm name
- `service_type` (string): Type of service/business
- `bio` (string): User biography

**Success Response (201 Created):**
```json
{
  "id": 1,
  "username": "john_farmer",
  "email": "john@example.com",
  "location": "Harare",
  "phone_number": "+263771234567",
  "business_name": "John's Farm",
  "service_type": "Farmer",
  "bio": "",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Response (400 Bad Request):**
```json
{
  "username": ["A user with that username already exists."],
  "email": ["This field must be unique."],
  "password": ["This password is too common."]
}
```

---

#### 1.2 Sign In

Authenticate existing user.

**Endpoint:** `POST /api/signin/`

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "john_farmer",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "username": "john_farmer",
  "email": "john@example.com",
  "location": "Harare",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "No active account found with the given credentials"
}
```

---

#### 1.3 Refresh Token

Get a new access token using refresh token.

**Endpoint:** `POST /api/auth/token/refresh/`

**Authentication:** Not required (uses refresh token)

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Note:** If `ROTATE_REFRESH_TOKENS` is enabled, a new refresh token is also returned.

---

#### 1.4 Verify Token

Verify if a token is valid.

**Endpoint:** `POST /api/auth/token/verify/`

**Authentication:** Not required

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response (200 OK):**
```json
{}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 2. Listing Endpoints

#### 2.1 List Listings

Get all active listings with pagination and filtering.

**Endpoint:** `GET /api/listings/`

**Authentication:** Required

**Query Parameters:**
- `listing_type` (string, optional): Filter by type (`product`, `service`, `supplier_product`)
- `category` (string, optional): Filter by category
- `location` (string, optional): Filter by location
- `status` (string, optional): Filter by status (default: `active`)
- `min_price` (number, optional): Minimum price filter
- `max_price` (number, optional): Maximum price filter
- `search` (string, optional): Search in name and description
- `page` (integer, optional): Page number for pagination
- `page_size` (integer, optional): Items per page (default: 20)

**Example Request:**
```http
GET /api/listings/?listing_type=product&category=Vegetables&location=Harare
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Success Response (200 OK):**
```json
{
  "count": 45,
  "next": "http://api.example.com/api/listings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "listing_type": "product",
      "name": "Fresh Tomatoes",
      "description": "Organic tomatoes from our farm",
      "price": "2.50",
      "unit": "kg",
      "location": "Harare",
      "category": "Vegetables",
      "status": "active",
      "organic": true,
      "user": {
        "id": 1,
        "username": "john_farmer",
        "business_name": "John's Farm"
      },
      "images": [
        {
          "id": 1,
          "image_url": "https://upcdn.io/abc123/tomatoes.jpg"
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### 2.2 Create Listing

Create a new listing.

**Endpoint:** `POST /api/listings/`

**Authentication:** Required

**Request Body:**
```json
{
  "listing_type": "product",
  "name": "Fresh Tomatoes",
  "description": "Organic tomatoes from our farm",
  "price": "2.50",
  "unit": "kg",
  "location": "Harare",
  "category": "Vegetables",
  "organic": true,
  "image_urls": [
    "https://upcdn.io/abc123/tomato1.jpg",
    "https://upcdn.io/abc123/tomato2.jpg"
  ]
}
```

**Required Fields:**
- `listing_type` (string): `product`, `service`, or `supplier_product`
- `name` (string): Listing name/title
- `price` (decimal): Price (must be > 0)
- `unit` (string): Price unit (kg, piece, hour, etc.)
- `location` (string): Location
- `description` (string): Detailed description

**Optional Fields:**
- `category` (string): Product/service category
- `organic` (boolean): For products only
- `provider` (string): For services only
- `supplier` (string): For supplier products only
- `status` (string): Default is `active`
- `image_urls` (array): Array of CDN image URLs

**Success Response (201 Created):**
```json
{
  "id": 1,
  "listing_type": "product",
  "name": "Fresh Tomatoes",
  "description": "Organic tomatoes from our farm",
  "price": "2.50",
  "unit": "kg",
  "location": "Harare",
  "category": "Vegetables",
  "status": "active",
  "organic": true,
  "user": {
    "id": 1,
    "username": "john_farmer"
  },
  "images": [
    {
      "id": 1,
      "image_url": "https://upcdn.io/abc123/tomato1.jpg"
    },
    {
      "id": 2,
      "image_url": "https://upcdn.io/abc123/tomato2.jpg"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### 2.3 Get Listing Detail

Retrieve a specific listing by ID.

**Endpoint:** `GET /api/listings/{listing_id}/`

**Authentication:** Required

**Path Parameters:**
- `listing_id` (integer): Listing ID

**Success Response (200 OK):**
```json
{
  "id": 1,
  "listing_type": "product",
  "name": "Fresh Tomatoes",
  "description": "Organic tomatoes from our farm",
  "price": "2.50",
  "unit": "kg",
  "location": "Harare",
  "category": "Vegetables",
  "status": "active",
  "organic": true,
  "user": {
    "id": 1,
    "username": "john_farmer",
    "email": "john@example.com",
    "business_name": "John's Farm",
    "phone_number": "+263771234567"
  },
  "images": [
    {
      "id": 1,
      "image_url": "https://upcdn.io/abc123/tomato1.jpg",
      "uploaded_at": "2024-01-15T10:30:00Z"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

#### 2.4 Update Listing

Update an existing listing (owner only).

**Endpoint:** `PUT /api/listings/{listing_id}/` or `PATCH /api/listings/{listing_id}/`

**Authentication:** Required (must be listing owner)

**Request Body (PATCH - partial update):**
```json
{
  "price": "3.00",
  "description": "Updated description with more details"
}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "name": "Fresh Tomatoes",
  "price": "3.00",
  "description": "Updated description with more details",
  ...
}
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

#### 2.5 Delete Listing

Delete a listing (owner only).

**Endpoint:** `DELETE /api/listings/{listing_id}/`

**Authentication:** Required (must be listing owner)

**Success Response (204 No Content):**
```
(No body)
```

---

#### 2.6 My Listings

Get all listings created by the authenticated user.

**Endpoint:** `GET /api/my-listings/`

**Authentication:** Required

**Query Parameters:**
- Same as List Listings endpoint

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Fresh Tomatoes",
    "price": "2.50",
    ...
  },
  {
    "id": 2,
    "name": "Organic Lettuce",
    "price": "1.50",
    ...
  }
]
```

---

### 3. Search Endpoints

#### 3.1 Semantic Search

Perform AI-powered semantic search across listings.

**Endpoint:** `GET /api/search/`

**Authentication:** Required

**Query Parameters:**
- `q` (string, required): Search query
- `type` (string, optional): Filter by model type (`listing`)
- `metadata__category` (string, optional): Filter by category
- `metadata__location` (string, optional): Filter by location
- `metadata__status` (string, optional): Filter by status
- `limit` (integer, optional): Number of results (default: 10)

**Example Request:**
```http
GET /api/search/?q=fresh organic vegetables&metadata__location=Harare&limit=20
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Success Response (200 OK):**
```json
{
  "query": "fresh organic vegetables",
  "results": [
    {
      "id": 1,
      "title": "Fresh Tomatoes",
      "description": "Organic tomatoes from our farm",
      "similarity_score": 0.92,
      "metadata": {
        "price": 2.50,
        "unit": "kg",
        "category": "Vegetables",
        "seller": "john_farmer",
        "sellerId": 1,
        "location": "Harare",
        "status": "active",
        "image": "https://upcdn.io/abc123/tomatoes.jpg",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      },
      "content_type": "listing",
      "object_id": 1
    }
  ],
  "total": 15
}
```

---

#### 3.2 Rebuild Search Index

Rebuild the entire search index for a model (admin only).

**Endpoint:** `POST /api/search/rebuild/`

**Authentication:** Required (admin only)

**Request Body:**
```json
{
  "app_label": "teseapi",
  "model_name": "listing"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Index rebuild started for teseapi.listing",
  "count": 150
}
```

---

### 4. Shopping Cart Endpoints

#### 4.1 Get Cart

Retrieve user's shopping cart.

**Endpoint:** `GET /api/cart/`

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "listing": {
        "id": 1,
        "name": "Fresh Tomatoes",
        "price": "2.50",
        "unit": "kg",
        "images": [...]
      },
      "quantity": 3,
      "price": "2.50",
      "subtotal": "7.50",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": "7.50",
  "item_count": 1
}
```

---

#### 4.2 Add to Cart

Add an item to the shopping cart.

**Endpoint:** `POST /api/cart/`

**Authentication:** Required

**Request Body:**
```json
{
  "listing_id": 1,
  "quantity": 3
}
```

**Success Response (201 Created):**
```json
{
  "id": 1,
  "listing": {
    "id": 1,
    "name": "Fresh Tomatoes"
  },
  "quantity": 3,
  "price": "2.50",
  "subtotal": "7.50"
}
```

---

#### 4.3 Update Cart Item

Update quantity of a cart item.

**Endpoint:** `PATCH /api/cart/{cart_item_id}/`

**Authentication:** Required

**Request Body:**
```json
{
  "quantity": 5
}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "quantity": 5,
  "subtotal": "12.50"
}
```

---

#### 4.4 Remove from Cart

Remove an item from the cart.

**Endpoint:** `DELETE /api/cart/{cart_item_id}/`

**Authentication:** Required

**Success Response (204 No Content):**
```
(No body)
```

---

### 5. Checkout & Payment Endpoints

#### 5.1 Create Order (Checkout)

Create an order from cart items.

**Endpoint:** `POST /api/checkout/`

**Authentication:** Required

**Request Body:**
```json
{
  "payment_method": "stripe",
  "shipping_info": {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "Harare",
    "phone": "+263771234567",
    "notes": "Please deliver in the morning"
  }
}
```

**Success Response (201 Created):**
```json
{
  "order": {
    "id": 1,
    "total_amount": "7.50",
    "status": "PENDING",
    "payment_method": "stripe",
    "items": [...],
    "shipping_info": {...},
    "created_at": "2024-01-15T10:30:00Z"
  },
  "payment": {
    "id": 1,
    "amount": "7.50",
    "method": "stripe",
    "status": "INITIATED",
    "client_secret": "pi_abc123_secret_xyz"
  }
}
```

**Client Next Steps:**
1. Use `client_secret` with Stripe.js to complete payment
2. Stripe redirects back after payment
3. Webhook updates order status

---

#### 5.2 Get Order

Retrieve order details.

**Endpoint:** `GET /api/orders/{order_id}/`

**Authentication:** Required (must be order owner)

**Success Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "john_farmer"
  },
  "total_amount": "7.50",
  "status": "PAID",
  "payment_method": "stripe",
  "items": [
    {
      "listing_id": 1,
      "name": "Fresh Tomatoes",
      "quantity": 3,
      "price": "2.50",
      "subtotal": "7.50"
    }
  ],
  "shipping_info": {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "Harare",
    "phone": "+263771234567"
  },
  "transaction_ref": "pi_abc123",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 6. Messaging Endpoints

#### 6.1 Get Conversations

List all conversations for the authenticated user.

**Endpoint:** `GET /api/messaging/conversations/`

**Authentication:** Required

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "participants": [
      {
        "id": 1,
        "username": "john_farmer"
      },
      {
        "id": 2,
        "username": "jane_buyer"
      }
    ],
    "last_message": {
      "id": 10,
      "content": "Is this still available?",
      "timestamp": "2024-01-15T12:00:00Z",
      "sender": "jane_buyer"
    },
    "unread_count": 2,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

---

#### 6.2 Get Messages

Retrieve messages in a conversation.

**Endpoint:** `GET /api/messaging/conversations/{conversation_id}/messages/`

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "conversation_id": 1,
  "messages": [
    {
      "id": 1,
      "sender": {
        "id": 1,
        "username": "john_farmer"
      },
      "content": "Hello! Yes, the tomatoes are still available.",
      "timestamp": "2024-01-15T10:30:00Z",
      "is_read": true
    },
    {
      "id": 2,
      "sender": {
        "id": 2,
        "username": "jane_buyer"
      },
      "content": "Great! Can I order 5kg?",
      "timestamp": "2024-01-15T10:35:00Z",
      "is_read": false
    }
  ]
}
```

---

#### 6.3 Send Message

Send a message in a conversation.

**Endpoint:** `POST /api/messaging/conversations/{conversation_id}/messages/`

**Authentication:** Required

**Request Body:**
```json
{
  "content": "Sure! I can prepare 5kg for you."
}
```

**Success Response (201 Created):**
```json
{
  "id": 3,
  "sender": {
    "id": 1,
    "username": "john_farmer"
  },
  "content": "Sure! I can prepare 5kg for you.",
  "timestamp": "2024-01-15T10:40:00Z",
  "is_read": false
}
```

---

## WebSocket API

### Connection

Connect to the WebSocket server for real-time updates.

**Endpoint:** `ws://api.example.com/ws/listings/`

**Authentication:** Include token in query string or headers

**Connection URL:**
```
ws://localhost:8000/ws/listings/?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Message Format

#### Server → Client (Listing Created)
```json
{
  "type": "listing.created",
  "data": {
    "id": 1,
    "name": "Fresh Tomatoes",
    "price": "2.50",
    ...
  }
}
```

#### Server → Client (Listing Updated)
```json
{
  "type": "listing.updated",
  "data": {
    "id": 1,
    "name": "Fresh Tomatoes",
    "price": "3.00",
    ...
  }
}
```

#### Server → Client (New Message)
```json
{
  "type": "message.received",
  "data": {
    "conversation_id": 1,
    "message": {
      "id": 3,
      "sender": "john_farmer",
      "content": "Hello!",
      "timestamp": "2024-01-15T10:40:00Z"
    }
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "code": "error_code",
  "field_errors": {
    "field_name": ["Error message for this field"]
  }
}
```

### Common Errors

#### Authentication Error
```json
{
  "detail": "Authentication credentials were not provided.",
  "code": "not_authenticated"
}
```

#### Validation Error
```json
{
  "price": ["Ensure this value is greater than or equal to 0.01."],
  "name": ["This field is required."]
}
```

#### Permission Error
```json
{
  "detail": "You do not have permission to perform this action.",
  "code": "permission_denied"
}
```

---

## Rate Limiting

### Current Limits
- **Default**: 100 requests per minute per user
- **Search**: 20 requests per minute per user
- **Authentication**: 10 requests per minute per IP

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 1673870400
```

### Rate Limit Exceeded Response
```json
{
  "detail": "Request was throttled. Expected available in 45 seconds.",
  "code": "throttled"
}
```

---

## Examples

### Complete Flow Example (Python)

```python
import requests

BASE_URL = "https://tesebackend-4ic7p.sevalla.app/api"

# 1. Sign up
signup_data = {
    "username": "john_farmer",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "location": "Harare"
}
response = requests.post(f"{BASE_URL}/signup/", json=signup_data)
tokens = response.json()
access_token = tokens["access"]

# 2. Create authorization header
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 3. Create a listing
listing_data = {
    "listing_type": "product",
    "name": "Fresh Tomatoes",
    "description": "Organic tomatoes",
    "price": "2.50",
    "unit": "kg",
    "location": "Harare",
    "category": "Vegetables"
}
response = requests.post(
    f"{BASE_URL}/listings/",
    json=listing_data,
    headers=headers
)
listing = response.json()
print(f"Created listing ID: {listing['id']}")

# 4. Search for listings
search_params = {"q": "organic vegetables"}
response = requests.get(
    f"{BASE_URL}/search/",
    params=search_params,
    headers=headers
)
results = response.json()
print(f"Found {results['total']} results")

# 5. Add to cart
cart_data = {
    "listing_id": listing['id'],
    "quantity": 3
}
response = requests.post(
    f"{BASE_URL}/cart/",
    json=cart_data,
    headers=headers
)

# 6. Checkout
checkout_data = {
    "payment_method": "stripe",
    "shipping_info": {
        "name": "John Doe",
        "address": "123 Main St",
        "city": "Harare",
        "phone": "+263771234567"
    }
}
response = requests.post(
    f"{BASE_URL}/checkout/",
    json=checkout_data,
    headers=headers
)
order = response.json()
print(f"Order created: {order['order']['id']}")
```

### JavaScript/TypeScript Example

```javascript
const BASE_URL = 'https://tesebackend-4ic7p.sevalla.app/api';

// 1. Sign in
async function signIn(username, password) {
  const response = await fetch(`${BASE_URL}/signin/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  return data;
}

// 2. Make authenticated request
async function fetchListings() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${BASE_URL}/listings/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return await response.json();
}

// 3. Create listing
async function createListing(listingData) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${BASE_URL}/listings/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(listingData),
  });
  
  return await response.json();
}

// 4. WebSocket connection
function connectWebSocket() {
  const token = localStorage.getItem('access_token');
  const ws = new WebSocket(`ws://localhost:8000/ws/listings/?token=${token}`);
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
    
    if (message.type === 'listing.created') {
      // Handle new listing
      updateListingsList(message.data);
    }
  };
  
  return ws;
}
```

---

## Postman Collection

A Postman collection is available for easy API testing:

**Import URL:**
```
https://api.example.com/docs/postman_collection.json
```

---

## API Changelog

### Version 1.0.0 (Current)
- Initial API release
- Authentication with JWT
- Listing management
- Semantic search
- Shopping cart
- Payment processing
- Real-time messaging

---

*Last Updated: 2024*
*API Version: 1.0.0*
