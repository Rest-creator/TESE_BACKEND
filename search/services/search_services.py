# search/services/search_services.py

import logging
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from pgvector.django import CosineDistance   # <-- FIXED: correct import
from ..models import SearchIndexEntry
from ..embeddings import generate_embedding

logger = logging.getLogger(__name__)


def index_object(obj, embed: bool = True):
    """
    Creates or updates a SearchIndexEntry for a Django model instance.
    """
    if not hasattr(obj, "to_search_document"):
        raise RuntimeError(f"{obj._meta.label} missing to_search_document method")

    doc = obj.to_search_document()

    # ---- Embedding text ----
    embedding_text = doc.get("embedding_text") or ""

    # ---- Generate AI embedding ----
    embedding = generate_embedding(embedding_text) if embed else None

    # Guarantee 768-dim vector (fallback)
    if not embedding:
        embedding = [0.0] * 768

    content_type = ContentType.objects.get_for_model(obj.__class__)

    entry, created = SearchIndexEntry.objects.update_or_create(
        content_type=content_type,
        object_id=obj.pk,
        defaults={
            "title": doc.get("title", "")[:255],
            "description": doc.get("description", ""),
            "metadata": {
                "category": doc.get("category", ""),
                "seller": doc.get("seller", ""),
                "location": doc.get("location", "")
            },
            "embedding": embedding,
        }
    )

    logger.info("Indexed %s:%s", obj._meta.label, obj.pk)
    return entry


def delete_object_from_index(obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    SearchIndexEntry.objects.filter(content_type=content_type, object_id=obj.pk).delete()
    logger.info("Deleted from index %s:%s", obj._meta.label, obj.pk)


def search_by_vector(query=None, filters=None, limit=10):
    """
    Semantic AI + Vector search using pgvector CosineDistance.
    Falls back to text search automatically.
    """
    filters = filters or {}

    if not query:
        return SearchIndexEntry.objects.none()

    # ---- Generate query embedding ----
    query_vec = generate_embedding(query)
    if not query_vec:
        return SearchIndexEntry.objects.none()

    try:
        qs = SearchIndexEntry.objects.all()

        # ---- Dynamic metadata filtering ----
        for fk, fv in filters.items():
            if fk.startswith("metadata__"):
                qs = qs.filter(**{fk: fv})

        # ---- Vector similarity ranking ----
        qs = qs.annotate(
            similarity=CosineDistance("embedding", query_vec)   # <-- FIXED
        ).order_by("similarity")[:limit]

        return qs

    except Exception as e:
        logger.warning("Vector search failed, falling back to text search: %s", e)

        # Fallback to classic text search
        return SearchIndexEntry.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:limit]
