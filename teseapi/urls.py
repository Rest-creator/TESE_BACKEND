# urls.py
from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# --- Auth Views ---
from .views_app.auth_views import SignupView, SigninView

# --- Unified Listing Views ---
from .views_app.listing_views import ListingListCreateView, ListingDetailView, MyListingsView

# --- Modular App Views / Legacy ViewSets ---
from .views_app.user_listings_view import UserListingsView
from modules.payment_module.implementation.payment_views import *

# --- WebSocket Consumers --- 
from .consumers import ProductConsumer

# Create a single router instance for all viewsets
router = DefaultRouter()
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"checkout", CheckoutViewSet, basename="checkout")


urlpatterns = router.urls

# ----------------------
# URL patterns
# ----------------------
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Auth endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),

    # JWT token endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Unified Listings endpoints
    path('listings/', ListingListCreateView.as_view(), name='listing-list-create'),
    path('listings/<int:listing_id>/', ListingDetailView.as_view(), name='listing-detail'),
    path('my-listings/', MyListingsView.as_view(), name='my-listings'),

    # Legacy / user-specific listings
    path('user-listings/', UserListingsView.as_view(), name='user-listings'),

    # WebSocket consumers
    re_path(r'ws/listings/$', ProductConsumer.as_asgi()),  # Can rename to ListingsConsumer if needed
]
