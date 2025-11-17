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

# --- WebSocket Consumers --- 
from .consumers import ProductConsumer

# Create a single router instance for all viewsets
router = DefaultRouter()

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

  ]
