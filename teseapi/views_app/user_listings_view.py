# views_app/user_listings_view.py
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from modules.listings.service.user_listings_service import UserListingsService
from modules.listings.serializer.listing_serializers import ListingReadSerializer


ROLE_TO_TYPE_MAP = {
    'farmer': 'product',
    'supplier': 'supplier_product',
    'service-provider': 'service',
    # customers can return empty list
}


class UserListingsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role_param = self.request.query_params.get('role', getattr(user, 'role', None))

        listing_type = ROLE_TO_TYPE_MAP.get(role_param)

        try:
            queryset = UserListingsService.get_listings(user, listing_type=listing_type)
        except ValueError as e:
            raise ValidationError(str(e))

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not queryset:
            return Response([])  # No listings for this user/role

        # Always use ListingReadSerializer now
        serializer = ListingReadSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
