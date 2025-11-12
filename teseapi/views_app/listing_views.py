# views/listing_views.py (updated portions)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from modules.listings.service.listing_service import ListingService
from modules.listings.serializer.listing_serializers import ListingReadSerializer
from modules.listings.serializer.listing_serializers import ListingWriteSerializer
import logging

logger = logging.getLogger(__name__)


class ListingListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        user_id = request.query_params.get("user_id")
        entities = ListingService.list_listings(user_id=int(user_id) if user_id else None)

        # Split listings into three arrays based on listing_type
        products = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "product"]
        services = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "service"]
        supplies = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "supplier_product"]

        return Response({
            "products": products,
            "services": services,
            "supplier_products": supplies
        }, status=status.HTTP_200_OK)

    def post(self, request):
        from modules.listings.serializer.listing_serializers import ListingWriteSerializer

        serializer = ListingWriteSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            entity = serializer.save()

            # Try to update search index (best-effort)
            try:
                # lazy import so this view still works if search isn't installed
                from search.services.search_services import index_object
                # index_object expects a model instance; ensure `entity` is instance
                index_object(entity)
            except Exception as e:
                logger.exception("Failed to index new listing (non-fatal): %s", e)

            # --- THIS IS THE FIX ---
            # You must serialize the instance before returning it
            data = ListingReadSerializer.from_entity(entity)
            return Response(data, status=status.HTTP_201_CREATED)
            # --- END OF FIX ---
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # In ListingDetailView...
    def get(self, request, listing_id=None):
        try:
            # You need a service method that gets ONE listing
            entity = ListingService.get_listing_by_id(listing_id) 
            
            if not entity:
                 return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize the single entity
            data = ListingReadSerializer.from_entity(entity)
            return Response(data, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error fetching listing detail: %s", e)
            return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def put(self, request, listing_id):
        serializer = ListingWriteSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            images = serializer.validated_data.pop("images", None)
            entity = ListingService.update_listing(
                listing_id=listing_id,
                user_id=request.user.id,
                payload=serializer.validated_data,
                images_files=images
            )
            data = ListingReadSerializer.from_entity(entity)

            # Update index (best-effort)
            try:
                from search.services.search_services import index_object
                index_object(entity)
            except Exception as e:
                logger.exception("Failed to update listing in search index (non-fatal): %s", e)

            return Response(data, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, listing_id):
        try:
            # Before deleting from DB, attempt to fetch the instance so we can remove it from index
            try:
                from django.apps import apps
                ListingModel = apps.get_model('listings', 'listing')
                instance = ListingModel.objects.get(pk=listing_id)
            except Exception:
                instance = None

            ListingService.delete_listing(listing_id=listing_id, user_id=request.user.id)

            # If we have the instance, try to remove from search index (best-effort)
            if instance is not None:
                try:
                    from search.services.search_services import delete_object_from_index
                    delete_object_from_index(instance)
                except Exception as e:
                    logger.exception("Failed to remove listing from search index (non-fatal): %s", e)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

class MyListingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entities = ListingService.list_listings(user_id=request.user.id)

        products = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "product"]
        services = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "service"]
        supplies = [ListingReadSerializer.from_entity(e) for e in entities if e.listing_type == "supplier_product"]

        return Response({
            "products": products,
            "services": services,
            "supplier_products": supplies
        }, status=status.HTTP_200_OK)
