# services/search_services.py
import logging
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from pgvector.django import CosineDistance
import google.generativeai as genai  # CHANGED: Import Google
from ..models import SearchIndexEntry

logger = logging.getLogger(__name__)

# Initialize Gemini (ensure GEMINI_API_KEY is in your settings.py)
# Get key here: https://aistudio.google.com/app/apikey
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_embedding(text, task_type="retrieval_document"):
    """
    Generates a vector embedding for a given text using Gemini.
    
    task_type options:
    - "retrieval_document": Used when indexing the database (storing items).
    - "retrieval_query": Used when the user is searching.
    """
    try:
        text = text.replace("\n", " ")  # Sanitize
        
        # CHANGED: Gemini API Call
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
    Takes a model instance (like Listing), generates an embedding, 
    and saves/updates it in SearchIndexEntry.
    """
    if not hasattr(instance, 'to_search_document'):
        logger.warning(f"Object {instance} does not implement to_search_document()")
        return

    doc_data = instance.to_search_document()
    
    # 'embedding_text' comes from your Listing.to_search_document method
    text_content = doc_data.get('embedding_text', '')
    
    # CHANGED: explicit task_type for better accuracy
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

    # CHANGED: explicit task_type for the search query
    query_vector = get_embedding(query, task_type="retrieval_query")
    
    if not query_vector:
        return SearchIndexEntry.objects.none()

    qs = SearchIndexEntry.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).order_by('distance')

    if filters:
        qs = qs.filter(**filters)

    return qs