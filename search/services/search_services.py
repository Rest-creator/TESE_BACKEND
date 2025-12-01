# services/search_services.py
import logging
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from pgvector.django import CosineDistance
import google.generativeai as genai
from ..models import SearchIndexEntry

logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# --- CONFIGURATION ---
# The cutoff score for semantic search.
# 0.0 = Identical
# 0.4 = Very relevant
# 0.55 = Roughly related
# 1.0 = Unrelated
# If results are too broad, LOWER this number (e.g., to 0.45).
# If you get no results often, RAISE this number (e.g., to 0.65).
SIMILARITY_THRESHOLD = 0.55

def get_embedding(text, task_type="retrieval_document"):
    """
    Generates a vector embedding for a given text using Gemini.
    """
    try:
        text = text.replace("\n", " ")  # Sanitize
        
        result = genai.embed_content(
            model="models/text-embedding-004", # 768 dimensions
            content=text,
            task_type=task_type,
            title="Embedding" if task_type == "retrieval_document" else None
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Error generating Gemini embedding: {e}")
        return None

def index_object(instance):
    """
    Takes a model instance, generates an embedding, and saves/updates it.
    """
    if not hasattr(instance, 'to_search_document'):
        logger.warning(f"Object {instance} does not implement to_search_document()")
        return

    doc_data = instance.to_search_document()
    text_content = doc_data.get('embedding_text', '')
    
    vector = get_embedding(text_content, task_type="retrieval_document")

    if not vector:
        return

    content_type = ContentType.objects.get_for_model(instance)
    
    SearchIndexEntry.objects.update_or_create(
        content_type=content_type,
        object_id=instance.id,
        defaults={
            'title': doc_data.get('title', str(instance)),
            'description': doc_data.get('description', ''),
            'metadata': doc_data,
            'embedding': vector 
        }
    )
    logger.info(f"Successfully indexed {instance}")

def delete_object_from_index(instance):
    content_type = ContentType.objects.get_for_model(instance)
    SearchIndexEntry.objects.filter(
        content_type=content_type, 
        object_id=instance.id
    ).delete()

def search_by_vector(query, filters=None):
    if not query:
        return SearchIndexEntry.objects.none()

    # 1. Generate Query Embedding
    query_vector = get_embedding(query, task_type="retrieval_query")
    
    if not query_vector:
        return SearchIndexEntry.objects.none()

    # 2. Build Query with Distance Calculation
    # We use 'alias' to calculate distance for filtering/ordering without 
    # necessarily attaching it to the final object output (unless you explicitly select it).
    qs = SearchIndexEntry.objects.alias(
        distance=CosineDistance('embedding', query_vector)
    )

    # 3. ✅ APPLY THRESHOLD (The "Cutoff")
    # This ensures we don't return random, unrelated items.
    qs = qs.filter(distance__lt=SIMILARITY_THRESHOLD)

    # 4. Apply Metadata Filters (if any)
    if filters:
        # e.g., filters={'metadata__category': 'Vegetables'}
        qs = qs.filter(**filters)

    # 5. Order by most similar
    qs = qs.order_by('distance')

    return qs