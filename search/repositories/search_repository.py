# search/repositories/search_repository.py
from typing import Dict, Any, Optional, List, Tuple
from django.db import connection
from django.db.models import QuerySet, Q
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

from search.models import SearchIndexEntry

logger = logging.getLogger(__name__)

# try to import pgvector django helpers (optional)
try:
    import pgvector  # type: ignore
    HAS_PGVECTOR = True
except Exception:
    HAS_PGVECTOR = False

# Import or implement your embedding function here (returns List[float])
# Implementations vary — see embeddings.py below for an example.
try:
    from ..services.embeddings import generate_embedding  # type: ignore
    HAS_EMBEDDINGS = True
except Exception:
    generate_embedding = None
    HAS_EMBEDDINGS = False


def parse_filters_for_queryset(raw_filters: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert query params like:
      metadata__price__lte=100  -> {"metadata__price__lte": 100}
      metadata__category=seed    -> {"metadata__category": "seed"}
    We return a dict that can be safely passed to .filter().
    Note: for sqlite fallback, we only support a limited set of lookups.
    """
    parsed = {}
    for k, v in raw_filters.items():
        # only accept keys starting with metadata__ or content_type__model
        if k.startswith("metadata__") or k == "content_type__model":
            # attempt to coerce numeric values
            if v is None:
                parsed[k] = None
                continue
            # try int then float, fallback to string
            if v.isdigit():
                parsed[k] = int(v)
            else:
                try:
                    parsed[k] = float(v)
                except Exception:
                    parsed[k] = v
    return parsed


def _portable_search(query: Optional[str], filters: Dict[str, str]) -> QuerySet:
    """
    Portable search for non-postgres environments (sqlite/local dev).
    Uses icontains on title/description and only simple metadata equality or
    simple metadata__<key> lookups. Returns a QuerySet (SearchIndexEntry).
    """
    q_obj = Q()
    if query:
        q_obj = Q(title__icontains=query) | Q(description__icontains=query)

    # content_type__model filter supports case-insensitive exact match
    if "content_type__model" in filters:
        model_name = filters.pop("content_type__model")
        q_obj &= Q(content_type__model__iexact=model_name)

    qs = SearchIndexEntry.objects.filter(q_obj).order_by("-created_at")

    # apply simple metadata equality filters (ignore complex ops for sqlite)
    for fk, fv in list(filters.items()):
        if fk.startswith("metadata__") and "__" not in fk[len("metadata__"):]:
            meta_key = fk[len("metadata__"):]
            qs = qs.filter(**{f"metadata__{meta_key}": fv})

    return qs


def _postgres_vector_search(
    query: str,
    filters: Dict[str, str],
    limit: int = 50,
) -> QuerySet:
    """
    Postgres + pgvector search implementation.

    This function:
    1. Calls generate_embedding(query) -> vector (list[float])
    2. Runs a SQL query that orders by embedding <-> query_vector (distance)
       and returns id list (SearchIndexEntry ids), then returns a QuerySet filtered
       by those ids in the same order.

    Notes:
    - This implementation constructs a parameterized SQL that casts the
      query vector literal to the pgvector type. It assumes pgvector extension
      is installed and the 'embedding' column is of type 'vector'.
    - generate_embedding must be implemented by you (OpenAI, HF, etc).
    """

    if not HAS_EMBEDDINGS or generate_embedding is None:
        raise ImproperlyConfigured(
            "Postgres vector search requested but no generate_embedding() available."
        )

    vec = generate_embedding(query)  # list[float]
    if not isinstance(vec, (list, tuple)) or len(vec) == 0:
        raise ValueError("generate_embedding returned invalid embedding")

    # create a textual literal of the vector in format: '[0.1,0.2, ...]' (pgvector accepts this with cast)
    # Note: we will pass the literal as a parameter to avoid SQL injection.
    vec_literal = "[" + ",".join(str(float(x)) for x in vec) + "]"

    # Build SQL with optional metadata filters (only some filters can be pushed into SQL easily).
    # We'll collect WHERE clauses and params.
    where_clauses = []
    params = []

    # optional content_type filter
    if "content_type__model" in filters:
        where_clauses.append("content_type_id IN (SELECT id FROM django_content_type WHERE model = %s)")
        params.append(filters["content_type__model"].lower())

    # For metadata filters, attempt simple JSONB lookups when numeric or string equality
    for fk, fv in list(filters.items()):
        if fk.startswith("metadata__") and "__" not in fk[len("metadata__"):]:
            meta_key = fk[len("metadata__"):]
            where_clauses.append("(metadata ->> %s) = %s")
            params.extend([meta_key, str(fv)])

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    sql = f"""
        SELECT id
        FROM search_searchindexentry
        WHERE {where_sql}
        ORDER BY embedding <-> %s
        LIMIT %s
    """

    # pass vector literal and limit as params
    params.extend([vec_literal, limit])

    # Execute SQL and collect ids
    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        ids = [r[0] for r in rows]

    if not ids:
        return SearchIndexEntry.objects.none()

    # Preserve ordering using an SQL CASE in ORM filter or use a manual ordering after fetch
    preserved = CaseOrdering(ids, "id")
    qs = SearchIndexEntry.objects.filter(id__in=ids).order_by(preserved)
    return qs


# helper to preserve ordering by a given id list (Django ORM friendly)
from django.db.models import Value, IntegerField, Case, When

def CaseOrdering(id_list: List[int], field_name: str = "id"):
    """
    Build an expression to order queryset in the same order as id_list:
      .order_by(CaseOrdering(ids, 'id'))
    """
    whens = [When(**{field_name: pk}, then=pos) for pos, pk in enumerate(id_list)]
    return Case(*whens, default=Value(len(id_list)), output_field=IntegerField())


def search_index(query: Optional[str], filters: Dict[str, str], limit: int = 50) -> QuerySet:
    """
    Main repository entrypoint used by the view.

    - Returns a Django QuerySet (SearchIndexEntry)
    - Will try to use pgvector on postgres if available
    - Falls back to portable icontains search otherwise
    """
    parsed_filters = parse_filters_for_queryset(filters.copy())

    vendor = connection.vendor
    if vendor == "postgresql" and HAS_PGVECTOR and HAS_EMBEDDINGS:
        try:
            return _postgres_vector_search(query or "", parsed_filters, limit=limit)
        except Exception as e:
            logger.exception("pgvector search failed, falling back: %s", e)
            # fall through to portable
            return _portable_search(query, parsed_filters)
    else:
        return _portable_search(query, parsed_filters)
