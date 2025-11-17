from rest_framework import viewsets
from .models import Listing
from .serializers.products_serializers import ListingSerializer
from .services.product_services import ListingService
import random
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Public access
            permission_classes = [AllowAny]
        else:
            # Authenticated access for create, update, delete
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        listing_type = self.request.query_params.get("listing_type")
        limit = self.request.query_params.get("limit")

        qs = ListingService.list_listings(
            user=user if user.is_authenticated else None,
            listing_type=listing_type
        )

        # Optional: shuffle only if limit is set
        if limit:
            limit = int(limit)
            ids = list(qs.values_list("id", flat=True))
            random.shuffle(ids)
            selected_ids = ids[:limit]
            return Listing.objects.filter(id__in=selected_ids)

        # Return all matching listings
        return qs


    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionError("Authentication required to create a listing")
        payload = self.request.data
        images = self.request.FILES.getlist("images")
        listing = ListingService.create_listing(self.request.user, payload, images)
        serializer.instance = listing

    def perform_update(self, serializer):
        listing = self.get_object()
        payload = self.request.data
        images = self.request.FILES.getlist("images")
        keep_images = self.request.data.getlist("existing_images_to_keep")
        updated = ListingService.update_listing(listing, payload, images, keep_images)
        serializer.instance = updated

    def perform_destroy(self, instance):
        ListingService.delete_listing(instance)

    @action(detail=False, methods=["get"], url_path="my-products", permission_classes=[IsAuthenticated])
    def my_products(self, request):
        user = request.user
        listings = Listing.objects.filter(user=user)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
