import logging
from django.contrib.contenttypes.models import ContentType
from ..models import SearchIndexEntry
from ..embeddings import generate_embedding
from django.db import models          # for F, JSONField, functions.Cast
from django.db.models import Q        # for Q(title__icontains=..., ...)

logger = logging.getLogger(__name__)

def index_object(obj, embed: bool = True):
    if not hasattr(obj, "to_search_document"):
        raise RuntimeError(f"{obj._meta.label} missing to_search_document method")

    doc = obj.to_search_document()
    embedding = doc.get("embedding") or (generate_embedding(doc["description"]) if embed else None)

    content_type = ContentType.objects.get_for_model(obj.__class__)
    entry, created = SearchIndexEntry.objects.update_or_create(
        content_type=content_type,
        object_id=obj.pk,
        defaults={
            "title": doc.get("title", "")[:255],
            "description": doc.get("description", ""),
            "metadata": doc.get("metadata", {}),
            # --- THIS IS THE OTHER FIX ---
            # Change the fallback from 384 to 768
            "embedding": embedding or [0.0]*768,  # store as vector
            # --- END OF FIX ---
        },
    )
    logger.info("Indexed %s:%s", obj._meta.label, obj.pk)
    return entry


def delete_object_from_index(obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    SearchIndexEntry.objects.filter(content_type=content_type, object_id=obj.pk).delete()
    logger.info("Deleted from index %s:%s", obj._meta.label, obj.pk)

def search_by_text(query: str, limit: int = 10):
    """
    Perform simple keyword search across indexed entries.
    For semantic search, replace with vector similarity search.
    """
    from django.db.models import Q
    return SearchIndexEntry.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    )[:limit]

from django.db.models import F
from pgvector.psycopg2 import vector  # optional helper

def search_by_vector(query=None, filters=None, limit=10):
    filters = filters or {}
    if not query:
        return SearchIndexEntry.objects.none()

    query_vec = generate_embedding(query)
    
    # Handle case where embedding generation fails
    if query_vec is None:
        return SearchIndexEntry.objects.none()

    try:
        qs = SearchIndexEntry.objects.all()
        for fk, fv in filters.items():
            if fk.startswith("metadata__"):
                meta_key = fk.replace("metadata__", "")
                qs = qs.filter(**{f"metadata__{meta_key}": fv})

        # pgvector semantic search
        qs = qs.annotate(
            similarity=models.functions.CosineDistance("embedding", query_vec)
        ).order_by("similarity")[:limit]

        return qs

    except Exception:
        # fallback for SQLite
        return SearchIndexEntry.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:limit]