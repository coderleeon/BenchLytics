import logging
from inference.gateway import RateLimiter
from inference.cache import SmartCache
from inference.batcher import DynamicBatcher

logger = logging.getLogger(__name__)

# Singletons for the lifecycle of the FastAPI app
rate_limiter = RateLimiter()
smart_cache = SmartCache()
dynamic_batcher = DynamicBatcher(max_batch_size=16, batch_window_ms=50)

class InferenceRouter:
    @staticmethod
    async def process_request(prompt: str, model_id: str, client_id: str = "default_user"):
        """
        Orchestrates the Inference Layer:
        1. Rate Limiting
        2. Caching
        3. Dynamic Batching / Generation
        """
        # 1. Rate Limiting
        allowed = await rate_limiter.acquire(client_id)
        if not allowed:
            raise Exception("429: Too Many Requests. Rate limit exceeded.")
        
        # 2. Caching (Exact + Semantic)
        try:
            cached_result = await smart_cache.get(prompt, model_id)
            if cached_result:
                # Returns (response_text, tokens, latency)
                return cached_result
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        # 3. Dynamic Batching (Generation)
        # Add to queue and wait for future resolution
        response_text, token_count, latency = await dynamic_batcher.add_request(prompt, model_id)

        # 4. Asynchronous Cache Update
        try:
            await smart_cache.set(prompt, model_id, response_text, token_count)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            
        return response_text, token_count, latency
