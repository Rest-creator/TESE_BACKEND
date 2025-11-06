# search/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import search_views

router = DefaultRouter()
router.register(r'index-admin', search_views.IndexAdminViewSet, basename='index-admin')

urlpatterns = [
    path('search/', search_views.SearchView.as_view(), name='search'),
    path('', include(router.urls)), # Includes all the admin-only URLs
]