from rest_framework import  permissions, status, views
from .serializers.search_serializer import SearchResultSerializer
from .models import SearchIndexEntry
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.apps import apps
from .permissions import IsAdminOrInternalService
from .services.search_services import index_object, search_by_vector

import logging
import traceback

logger = logging.getLogger(__name__)

class SearchView(views.APIView):
    """
    Performs semantic search.
    If matches are found -> Returns them with found=True.
    If NO matches are found -> Returns random available products with found=False.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        query = self.request.query_params.get('q', '').strip()
        
        # 1. Collect Filters
        filters = {}
        for key, value in self.request.query_params.items():
            if key.startswith('metadata__'):
                filters[key] = value
            if key == 'type':
                filters['content_type__model'] = value

        # 2. Initialize Result Variables
        qs = None
        found = False
        message = ""

        # 3. Attempt Vector Search
        if query:
            try:
                # search_by_vector should handle the "threshold" logic internally
                # and return an empty queryset if distances are too high.
                qs = search_by_vector(query=query, filters=filters)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
                logger.debug(traceback.format_exc())
                qs = None

        # 4. Check Results & Handle Fallback
        # If we have a query, and vector search returned results:
        if qs is not None and qs.exists():
            found = True
            message = "Matches found"
        else:
            # --- FALLBACK SCENARIO ---
            found = False
            if query:
                message = f"No exact matches for '{query}'. Here are some available products."
            else:
                message = "Discover our products."

            # Fetch random available items from the index to keep the user engaged
            # Note: .order_by('?') is expensive on massive DBs, but fine for MVP/startups
            qs = SearchIndexEntry.objects.all().order_by('?')[:12]

            # Apply type filter to fallback if it exists (so we don't show services when looking for products)
            if 'content_type__model' in filters:
                qs = qs.filter(content_type__model__iexact=filters['content_type__model'])

        # 5. Serialize
        serializer = SearchResultSerializer(qs, many=True)

        # 6. Return Custom Response Structure
        return Response({
            "results": serializer.data,
            "found": found,
            "message": message
        }, status=status.HTTP_200_OK)


class IndexAdminViewSet(viewsets.ViewSet):
    """
    Admin endpoints for managing the search index.
    Implements: POST /search/index/, DELETE /search/index/{id},
                POST /search/bulk/, POST /search/rebuild/
    """
    permission_classes = [IsAdminOrInternalService]

    def create(self, request):
        """
        (POST /search/index/)
        Manually indexes a single object.
        Expects: { "app_label": "listings", "model_name": "listing", "object_id": 123 }
        """
        app_label = request.data.get('app_label')
        model_name = request.data.get('model_name')
        object_id = request.data.get('object_id')

        try:
            Model = apps.get_model(app_label, model_name)
            instance = Model.objects.get(pk=object_id)
        except Exception as e:
            return Response({"error": f"Object not found: {e}"}, status=status.HTTP_404_NOT_FOUND)
        
        index_object(instance) # Run the service
        return Response({"status": "indexed", "object_id": object_id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        (DELETE /search/index/{id}/)
        Deletes a single entry *from the index*.
        'pk' here is the ID of the SearchIndexEntry itself.
        """
        try:
            index_entry = SearchIndexEntry.objects.get(pk=pk)
            obj_repr = str(index_entry)
            index_entry.delete()
            return Response({"status": "deleted", "entry": obj_repr}, status=status.HTTP_204_NO_CONTENT)
        except SearchIndexEntry.DoesNotExist:
            return Response({"error": "Index entry not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def rebuild(self, request):
        """
        (POST /search/rebuild/)
        Rebuilds the entire index for a given model.
        Expects: { "app_label": "listings", "model_name": "listing" }
        """
        app_label = request.data.get('app_label')
        model_name = request.data.get('model_name')
        
        try:
            Model = apps.get_model(app_label, model_name)
        except LookupError:
            return Response({"error": f"Model {app_label}.{model_name} not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Clear existing entries for this model
        ContentType = apps.get_model('contenttypes', 'ContentType')
        content_type = ContentType.objects.get_for_model(Model)
        SearchIndexEntry.objects.filter(content_type=content_type).delete()
        
        count = 0
        for instance in Model.objects.all():
            index_object(instance)
            count += 1
            
        return Response({"status": "rebuild complete", "model": model_name, "indexed_items": count})