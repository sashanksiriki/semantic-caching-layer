"""
The cache itself: a vector store (Chroma, persisted to disk) that maps
prompt embeddings -> stored responses.

Three responsibilities live here, on purpose kept in one class because
they all operate on the same underlying collection:
  1. lookup()  - nearest-neighbor search + threshold check + TTL check
  2. add()     - write a new entry after a cache miss
  3. eviction  - keep the cache from growing forever (LRU by last_accessed)
"""
import time
import uuid

import chromadb

from app.config import settings
from app.embeddings import embed


class SemanticCache:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="semantic_cache",
            metadata={"hnsw:space": "cosine"},
        )

    def lookup(self, normalized_prompt: str) -> dict | None:
        if self.collection.count() == 0:
            return None

        q_embedding = embed(normalized_prompt)
        results = self.collection.query(query_embeddings=[q_embedding], n_results=1)

        if not results["ids"][0]:
            return None

        entry_id = results["ids"][0][0]
        distance = results["distances"][0][0]
        similarity = 1 - distance
        meta = results["metadatas"][0][0]

        # Expired entries don't count as hits, and we clean them up
        # opportunistically instead of running a separate sweep job.
        if time.time() - meta["created_at"] > settings.cache_ttl_seconds:
            self.collection.delete(ids=[entry_id])
            return None

        if similarity < settings.similarity_threshold:
            return None

        meta["last_accessed"] = time.time()
        meta["hit_count"] = meta.get("hit_count", 0) + 1
        self.collection.update(ids=[entry_id], metadatas=[meta])

        return {
            "response": meta["response"],
            "similarity": round(similarity, 4),
            "original_prompt": meta["original_prompt"],
        }

    def add(self, normalized_prompt: str, original_prompt: str, response: str) -> None:
        self._evict_if_full()
        now = time.time()
        self.collection.add(
            embeddings=[embed(normalized_prompt)],
            documents=[normalized_prompt],
            metadatas=[
                {
                    "response": response,
                    "original_prompt": original_prompt,
                    "created_at": now,
                    "last_accessed": now,
                    "hit_count": 0,
                }
            ],
            ids=[str(uuid.uuid4())],
        )

    def _evict_if_full(self) -> None:
        count = self.collection.count()
        if count < settings.max_cache_size:
            return

        all_items = self.collection.get(include=["metadatas"])
        items = list(zip(all_items["ids"], all_items["metadatas"]))
        items.sort(key=lambda pair: pair[1].get("last_accessed", 0))

        overflow = count - settings.max_cache_size + 1
        to_remove = [item_id for item_id, _ in items[:overflow]]
        self.collection.delete(ids=to_remove)

    def stats(self) -> dict:
        return {"total_entries": self.collection.count()}


# Singleton instance used by the API layer.
cache = SemanticCache()
