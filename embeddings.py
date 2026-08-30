"""
Embedding layer. Turns text into a vector so we can compare prompts by
meaning instead of exact string match.

Model is loaded once and cached (it's ~80MB and takes a second or two
to load) rather than reloaded per-request.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
