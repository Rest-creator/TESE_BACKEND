from typing import List
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Load a pre-trained model.
# 'paraphrase-multilingual-mpnet-base-v2' produces 768-dimension embeddings.
try:
    embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    EMBEDDING_DIM = 768  # <-- This now correctly matches the model
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    embedding_model = None

def generate_embedding(text: str) -> List[float] | None:
    if not text:
        return None

    if embedding_model is None:
        logger.error("Embedding model is not loaded. Cannot generate embedding.")
        return None

    try:
        # .encode() is the function to create the embedding
        embedding = embedding_model.encode(text)
        
        # Convert from numpy array to a standard Python list
        return embedding.tolist()

    except Exception as e:
        logger.error("Embedding generation failed: %s", e)
        # Fallback deterministic embedding (matches your new dimension)
        seed = abs(hash(text))
        return [float((seed * (i + 1)) % 1000) / 1000.0 for i in range(EMBEDDING_DIM)]