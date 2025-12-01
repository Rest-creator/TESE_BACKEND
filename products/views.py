from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Listing
from .serializers.products_serializers import ListingSerializer
from .services.product_services import ListingService
import random
from django.db.models import Q

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]  # public access
        else:
            permission_classes = [IsAuthenticated]  # auth required
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Logic:
        1. If 'search' param exists -> Search name/description/category
        2. If 'listing_type' param exists -> Filter by type
        3. If NO search -> Return 10 random items (Discovery Mode)
        """
        qs = ListingService.list_listings(user=None) # Get base queryset

        # 1. Capture parameters
        search_query = self.request.query_params.get("search", None)
        listing_type = self.request.query_params.get("listing_type", None)
        limit = self.request.query_params.get("limit", None)

        # 2. Filter by Type (e.g., ?type=product)
        if listing_type:
            qs = qs.filter(listing_type=listing_type)

        # 3. Search Logic
        if search_query:
            # Simple case-insensitive search on Name, Description, or Category
            qs = qs.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(category__icontains=search_query)
            )
        
        # 4. Randomize ONLY if it's an initial load (no search)
        else:
            # Default to 10 items if limit is not provided
            limit_count = int(limit) if limit else 10
            
            # Efficient random selection for smaller datasets
            ids = list(qs.values_list("id", flat=True))
            if ids:
                random.shuffle(ids)
                selected_ids = ids[:limit_count]
                qs = qs.filter(id__in=selected_ids)

        return qs
    
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionError("Authentication required to create a listing")
        payload = self.request.data
        
        # ✅ CAPTURE MULTIPLE IMAGES
        images = self.request.FILES.getlist("images")
        
        listing = ListingService.create_listing(self.request.user, payload, images)
        serializer.instance = listing

    def perform_update(self, serializer):
        listing = self.get_object()
        payload = self.request.data
        
        # ✅ CAPTURE MULTIPLE IMAGES
        images = self.request.FILES.getlist("images")
        
        # ✅ CAPTURE LIST OF IMAGES TO KEEP
        keep_images = self.request.data.getlist("existing_images_to_keep")
        
        updated = ListingService.update_listing(listing, payload, images, keep_images)
        serializer.instance = updated

    def perform_destroy(self, instance):
        ListingService.delete_listing(instance)

    @action(
        detail=False,
        methods=["get"],
        url_path="my-products",
        permission_classes=[IsAuthenticated]
    )
    def my_products(self, request):
        """
        Return only the listings uploaded by the current user.
        """
        # Pass a flag so the service filters by this user
        user = request.user
        setattr(user, "filter_by_user", True)
        listings = ListingService.list_listings(user=user)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)