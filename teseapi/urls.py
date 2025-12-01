# urls.py
from django.urls import path,  include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from teseapi.views_app.profile_views import UserProfileView 
from .views_app.auth_views import SignupView, SigninView
from .views_app.reset_password import RequestPasswordResetView, ResetPasswordConfirmView


# Create a single router instance for all viewsets
router = DefaultRouter()

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Auth endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # JWT token endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('auth/password-reset-request/', RequestPasswordResetView.as_view(), name='password-reset-request'),
    path('auth/password-reset-confirm/', ResetPasswordConfirmView.as_view(), name='password-reset-confirm'),

  ]
