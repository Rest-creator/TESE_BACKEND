from typing import List
import os
import hashlib

def generate_embedding(text: str) -> List[float]:
    """
    Replace this with a real embedding provider (OpenAI, HuggingFace, local model).
    Currently returns a deterministic vector for testing.
    """
    if not text:
        return []

    dim = int(os.environ.get("EMBED_DIM", 384))
    # cheap deterministic pseudo-embedding
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return [float((seed * (i + 1)) % 1000) / 1000.0 for i in range(dim)]
