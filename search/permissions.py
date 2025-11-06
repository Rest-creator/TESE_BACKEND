# search/permissions.py
from rest_framework import permissions
from django.conf import settings

class IsAdminOrInternalService(permissions.BasePermission):
    """
    Allows access only to admin users (is_staff) or
    internal services providing a valid service token.
    """

    def has_permission(self, request, view):
        # 1. Check for admin user (e.g., logged into Django admin)
        if request.user and request.user.is_staff:
            return True

        # 2. Check for internal service token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return False

        try:
            # We expect a header like: "Token YOUR_SECRET_SERVICE_TOKEN"
            auth_type, token = auth_header.split(' ')
            if auth_type.lower() != 'token':
                return False
        except ValueError:
            return False # Header was malformed

        # Use a hard-coded token from settings for simplicity.
        # A more robust system might use Django Rest Knox or JWT.
        INTERNAL_SERVICE_TOKEN = getattr(settings, 'INTERNAL_SERVICE_TOKEN', None)
        
        # Compare securely
        return INTERNAL_SERVICE_TOKEN and token == INTERNAL_SERVICE_TOKEN