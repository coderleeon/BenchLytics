import hashlib
import json
import logging
import time
import numpy as np
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer
import faiss

logger = logging.getLogger(__name__)

class SmartCache:
    def __init__(self, redis_url="redis://localhost:6379", similarity_threshold=0.98):
        self.redis_url = redis_url
        self._redis = None
        self.threshold = similarity_threshold
        
        # Load small/fast embedding model
        logger.info("Loading sentence-transformers for Semantic Cache...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = self.embedder.get_sentence_embedding_dimension()
        
        # In-memory FAISS index (Inner Product)
        self.index = faiss.IndexFlatIP(self.vector_dim)
        
        # Mapping from faiss index ID to cache metadata payload
        self.meta_store = {}
        self._current_id = 0

    async def get_redis(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def get(self, prompt: str, model_id: str):
        redis = await self.get_redis()
        
        # 1. Exact Match via Redis (O(1))
        exact_key = f"cache:exact:{model_id}:{hashlib.sha256(prompt.encode()).hexdigest()}"
        cached_exact = await redis.get(exact_key)
        if cached_exact:
            logger.info("Exact Cache Hit")
            payload = json.loads(cached_exact)
            return payload['response'], 0, 2.0  # response, tokens, latency=2ms

        # 2. Semantic Match via FAISS
        if self._current_id == 0:
            return None

        embedding = self.embedder.encode([prompt], normalize_embeddings=True)
        distances, indices = self.index.search(embedding.astype('float32'), 1)
        
        best_idx = indices[0][0]
        best_dist = distances[0][0]

        if best_idx != -1 and best_dist >= self.threshold:
            meta = self.meta_store.get(best_idx)
            if meta and meta['model_id'] == model_id:
                logger.info(f"Semantic Cache Hit (Distance: {best_dist:.3f})")
                return meta['response'], 0, 30.0  # fake 30ms latency for semantic

        return None
        
    async def set(self, prompt: str, model_id: str, response: str, tokens: int):
        redis = await self.get_redis()
        
        # Add to exact cache (TTL 24 hours)
        exact_key = f"cache:exact:{model_id}:{hashlib.sha256(prompt.encode()).hexdigest()}"
        payload = json.dumps({"response": response, "tokens": tokens})
        await redis.set(exact_key, payload, ex=86400)
        
        # Add to semantic cache
        embedding = self.embedder.encode([prompt], normalize_embeddings=True)
        self.index.add(embedding.astype('float32'))
        
        self.meta_store[self._current_id] = {
            "model_id": model_id,
            "response": response,
            "prompt": prompt,
            "tokens": tokens
        }
        self._current_id += 1
