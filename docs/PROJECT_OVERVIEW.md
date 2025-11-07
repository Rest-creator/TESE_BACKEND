# TESE Marketplace - Project Overview

## Table of Contents
1. [Introduction](#introduction)
2. [Project Vision](#project-vision)
3. [Core Features](#core-features)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Key Differentiators](#key-differentiators)
7. [Target Users](#target-users)
8. [Business Model](#business-model)

---

## Introduction

**TESE Marketplace** is a comprehensive, full-featured e-commerce platform backend built with Django and Django REST Framework. It provides a robust foundation for online marketplaces specializing in agricultural products, services, and supplier networks. The platform is designed with scalability, modularity, and modern web standards in mind.

### Project Name
- **Name**: TESE Marketplace Backend
- **Version**: 1.0.0
- **Framework**: Django 5.2.3
- **API Framework**: Django REST Framework 3.16.0

### Repository Information
- **Location**: `Backend/`
- **Main Application**: `teseapp`
- **API Module**: `teseapi`

---

## Project Vision

TESE Marketplace aims to create a modern, efficient digital marketplace that connects:
- **Farmers** with consumers seeking fresh agricultural products
- **Service providers** offering agricultural and related services
- **Suppliers** providing agricultural inputs, tools, and equipment
- **Consumers** looking for quality products and services

The platform emphasizes:
- **Transparency**: Clear pricing, product descriptions, and seller information
- **Accessibility**: Easy-to-use APIs for web and mobile applications
- **Scalability**: Built to handle growing user bases and transaction volumes
- **Security**: JWT-based authentication and secure payment processing
- **Intelligence**: Semantic search capabilities powered by AI/ML

---

## Core Features

### 1. **User Management & Authentication**
- Custom user model extending Django's AbstractUser
- JWT-based authentication (access + refresh tokens)
- Token blacklisting for security
- User profiles with business information
- Location-based user data
- Phone number verification support

### 2. **Multi-Type Listing System**
Unified listing model supporting three types:
- **Products**: Physical agricultural products (vegetables, fruits, grains, etc.)
- **Services**: Agricultural services (farming, consultation, delivery, etc.)
- **Supplier Products**: Agricultural inputs and equipment

Each listing includes:
- Name, description, and pricing
- Location information
- Category classification
- Status tracking (active/inactive)
- Image gallery support via Bytescale CDN
- User ownership and timestamps

### 3. **Advanced Search Capabilities**
- **Semantic Search**: AI-powered vector-based search using sentence transformers
- **Embedding Storage**: pgvector integration for efficient similarity search
- **Metadata Filtering**: Filter by category, location, price, seller, etc.
- **SQLite Fallback**: Plain text search when vector database unavailable
- **Real-time Indexing**: Automatic indexing of new listings

### 4. **E-Commerce Functionality**
- **Shopping Cart**: User-specific cart management
- **Order Processing**: Complete order lifecycle management
- **Payment Integration**: 
  - Stripe for international payments
  - PayNow for local payments (Zimbabwe)
- **Transaction Tracking**: Comprehensive payment and order history
- **Shipping Information**: JSON-based flexible shipping data

### 5. **Messaging System**
- Real-time messaging between buyers and sellers
- WebSocket support via Django Channels
- Redis-backed channel layer for scalability
- Message persistence and history
- Conversation threading

### 6. **Image Management**
- Bytescale CDN integration for image hosting
- Generic foreign key support for multiple model types
- Optimized image delivery via CDN
- Default placeholder images
- Bulk image upload support

### 7. **Real-time Features**
- WebSocket connections for live updates
- Real-time product listings
- Live messaging notifications
- Channel-based event broadcasting

---

## Technology Stack

### Backend Framework
- **Django 5.2.3**: Core web framework
- **Django REST Framework 3.16.0**: RESTful API development
- **Python 3.x**: Programming language

### Authentication & Security
- **djangorestframework-simplejwt 5.5.0**: JWT authentication
- **django-cors-headers 4.7.0**: Cross-origin resource sharing

### Database & Search
- **PostgreSQL** (Production): Primary database with vector support
- **SQLite3** (Development): Local development database
- **pgvector**: Vector similarity search
- **psycopg2-binary 2.9.10**: PostgreSQL adapter

### AI/ML & Search
- **transformers 4.57.0**: Hugging Face transformers
- **torch 2.9.0**: PyTorch for ML models
- **sentence-transformers**: Embedding generation
- **tokenizers 0.22.1**: Text tokenization

### Real-time Communication
- **channels 4.2.2**: WebSocket support
- **channels-redis 4.2.1**: Redis channel layer
- **Redis**: Message broker and cache

### Payment Processing
- **stripe 12.5.0**: International payment processing
- **paynow 1.0.8**: Local payment gateway (Zimbabwe)

### External Services
- **Bytescale**: Image CDN and storage
- **twilio 9.6.4**: SMS notifications (optional)
- **requests 2.32.5**: HTTP client

### Deployment
- **gunicorn 21.2.0**: WSGI HTTP server
- **python-dotenv 1.1.1**: Environment variable management
- **Procfile**: Heroku/Sevalla deployment configuration

### Additional Libraries
- **tenacity 9.1.2**: Retry logic
- **vaderSentiment 3.3.2**: Sentiment analysis
- **unstructured**: Document processing
- **xgboost 3.0.5**: Machine learning

---

## Project Structure

```
Backend/
├── docs/                          # Documentation files
├── modules/                       # Feature modules
│   ├── auth/                     # Authentication module
│   │   ├── entities/             # Domain entities
│   │   ├── repositories/         # Data access layer
│   │   ├── serializers/          # API serializers
│   │   └── services/             # Business logic
│   ├── listings/                 # Listing management
│   │   ├── entities/
│   │   ├── repository/
│   │   ├── serializer/
│   │   └── service/
│   ├── messaging/                # Real-time messaging
│   │   ├── Implementation/
│   │   ├── entities/
│   │   ├── repositories/
│   │   ├── serializers/
│   │   └── services/
│   ├── payment_module/           # Payment processing
│   │   ├── entities/
│   │   ├── gateways/
│   │   ├── implementation/
│   │   ├── repositories/
│   │   ├── serializers/
│   │   └── services/
│   └── utils/                    # Shared utilities
├── search/                       # Semantic search module
│   ├── repositories/
│   ├── serializers/
│   ├── services/
│   └── tests/
├── teseapi/                      # Main API application
│   ├── views_app/               # View controllers
│   │   ├── auth_views.py
│   │   ├── listing_views.py
│   │   ├── service_views.py
│   │   ├── supplier_views.py
│   │   └── user_listings_view.py
│   ├── consumers.py             # WebSocket consumers
│   ├── models.py                # Database models
│   ├── permissions.py           # Custom permissions
│   ├── routing.py               # WebSocket routing
│   └── urls.py                  # API URL routing
├── teseapp/                      # Project configuration
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL configuration
│   ├── asgi.py                  # ASGI configuration
│   └── wsgi.py                  # WSGI configuration
├── product_images/               # Media files storage
├── db.sqlite3                   # SQLite database (dev)
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment configuration
└── .gitignore                   # Git ignore rules
```

---

## Key Differentiators

### 1. **Clean Architecture**
- Separation of concerns with entities, repositories, services, and serializers
- Domain-driven design principles
- Modular structure for easy maintenance and testing

### 2. **AI-Powered Search**
- Semantic search using machine learning embeddings
- More accurate search results compared to traditional keyword search
- Understands context and meaning, not just exact matches

### 3. **Multi-Gateway Payment Support**
- Flexible payment system supporting multiple providers
- Easy to add new payment gateways
- Localized payment methods for regional markets

### 4. **Real-time Capabilities**
- WebSocket support for instant updates
- Live messaging between users
- Event-driven architecture

### 5. **Scalable Infrastructure**
- PostgreSQL with vector extensions for production
- Redis for caching and real-time features
- CDN integration for media files
- Gunicorn for production deployment

### 6. **Developer-Friendly**
- Comprehensive API documentation
- RESTful design principles
- JWT authentication for stateless API access
- CORS support for cross-origin requests

---

## Target Users

### Primary Users
1. **Farmers & Agricultural Producers**
   - List and sell their products
   - Manage inventory
   - Track orders and payments

2. **Service Providers**
   - Offer agricultural services
   - Manage bookings
   - Build reputation

3. **Suppliers**
   - List agricultural inputs and equipment
   - Bulk order management
   - B2B transactions

4. **Consumers**
   - Browse and search products
   - Make purchases
   - Communicate with sellers

### Secondary Users
1. **Platform Administrators**
   - Content moderation
   - User management
   - Analytics and reporting

2. **Third-party Developers**
   - API integration
   - Mobile app development
   - Custom integrations

---

## Business Model

### Revenue Streams
1. **Transaction Fees**: Commission on completed sales
2. **Premium Listings**: Featured placement for sellers
3. **Subscription Plans**: Monthly/annual seller subscriptions
4. **Payment Processing Fees**: Markup on payment gateway fees

### Value Propositions

**For Sellers:**
- Access to a larger customer base
- Easy-to-use listing management
- Secure payment processing
- Built-in marketing tools

**For Buyers:**
- Wide variety of products and services
- Verified sellers and ratings
- Secure transactions
- Advanced search capabilities

**For the Platform:**
- Scalable technology stack
- Low operational overhead
- Multiple revenue streams
- Data-driven insights

---

## Future Roadmap

### Phase 1 (Current)
- ✅ Core marketplace functionality
- ✅ User authentication and authorization
- ✅ Listing management
- ✅ Payment integration
- ✅ Semantic search

### Phase 2 (Planned)
- 📋 Mobile application API enhancements
- 📋 Advanced analytics dashboard
- 📋 Rating and review system
- 📋 Seller verification system
- 📋 Multi-language support

### Phase 3 (Future)
- 📋 Machine learning recommendations
- 📋 Predictive pricing
- 📋 Inventory management automation
- 📋 Logistics integration
- 📋 Advanced seller tools

---

## Success Metrics

### Technical Metrics
- API response time < 200ms (p95)
- 99.9% uptime
- Zero security breaches
- < 1% error rate

### Business Metrics
- User growth rate
- Transaction volume
- Seller retention rate
- Customer satisfaction score
- Revenue per user

---

## Contact & Support

### Development Team
- **Project Lead**: [Your Name]
- **Backend Development**: Django Team
- **DevOps**: Infrastructure Team

### Documentation
- **Technical Docs**: `/docs/`
- **API Reference**: `/docs/API_DOCUMENTATION.md`
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md`

### Resources
- **Live API**: https://tesebackend-4ic7p.sevalla.app/api/
- **Frontend**: https://tese-dvx.pages.dev
- **Admin Panel**: https://swapback.zchpc.ac.zw/admin/

---

*Last Updated: 2024*
*Version: 1.0.0*
