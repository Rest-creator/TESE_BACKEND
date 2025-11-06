from rest_framework import generics, permissions
from .serializers.search_serializer import SearchResultSerializer
from .repositories.search_repository import search_index
from .models import *
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.apps import apps
from .permissions import IsAdminOrInternalService
from .services.search_services import index_object, delete_object_from_index, search_by_vector

from django.db import connection
from django.db.models import Q
import logging, traceback

logger = logging.getLogger(__name__)

class SearchView(generics.ListAPIView):
    serializer_class = SearchResultSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('q', None)
        # collect metadata-like filters (keep previous behavior)
        filters = {}
        for key, value in self.request.query_params.items():
            if key.startswith('metadata__'):
                filters[key] = value
            if key == 'type':
                filters['content_type__model'] = value

        # If no query and no filters, keep previous behavior (empty set)
        if not query and not filters:
            return SearchIndexEntry.objects.none()

        # First attempt: delegate to repository (may use pgvector/postgres-specific SQL)
        try:
            # Only attempt repo search if repo exists
            qs = search_by_vector(query=query, filters=filters)
            # Ensure repo returned a queryset-like object; if not, try to convert
            if qs is None:
                raise RuntimeError("search_index returned None")
            return qs
        except Exception as e:
            # Log helpful debug info (DB vendor, query, filters, traceback)
            logger.error(
                "search_index() failed. DB vendor=%s q=%r filters=%s error=%s",
                connection.vendor,
                query,
                filters,
                str(e),
            )
            logger.debug(traceback.format_exc())

            # Fallback: perform portable icontains search on SearchIndexEntry
            # This avoids any Postgres-only SQL and keeps the endpoint working on sqlite/local dev.
            try:
                q_obj = Q()
                if query:
                    q_obj = Q(title__icontains=query) | Q(description__icontains=query)

                # Apply content_type filter if provided
                if 'content_type__model' in filters:
                    model_name = filters.pop('content_type__model')
                    q_obj &= Q(content_type__model__iexact=model_name)

                base_qs = SearchIndexEntry.objects.filter(q_obj).order_by('-created_at')

                # Apply any simple metadata filters if they map directly to JSON lookups
                # NOTE: SQLite won't support jsonfield lookups robustly — keep to simple equality
                for fk, fv in list(filters.items()):
                    # only handle "metadata__key" style simple equality (metadata__price__lte not handled here)
                    if fk.startswith('metadata__') and '__' not in fk[len('metadata__'):]:
                        meta_key = fk.replace('metadata__', '')
                        base_qs = base_qs.filter(**{f"metadata__{meta_key}": fv})
                        
                print(base_qs)

                return base_qs
            except Exception as fallback_exc:
                logger.exception("Fallback search also failed: %s", fallback_exc)
                # final safe fallback: empty queryset so view returns empty results (instead of 500)
                return SearchIndexEntry.objects.none()

class IndexAdminViewSet(viewsets.ViewSet):
    """
    Admin endpoints for managing the search index.
    Implements: POST /search/index/, DELETE /search/index/{id},
                POST /search/bulk/, POST /search/rebuild/
    """
    # Apply our custom permission class to all actions in this ViewSet
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
        
        # TODO: This should be a background task!
        # Running this in a request will time out.
        count = 0
        for instance in Model.objects.all():
            index_object(instance)
            count += 1
            
        return Response({"status": "rebuild complete", "model": model_name, "indexed_items": count})

    # You would also add a 'bulk' action here (POST /search/bulk/)
    # that takes a list of object IDs to index.