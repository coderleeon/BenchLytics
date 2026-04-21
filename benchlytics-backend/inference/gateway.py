import time
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_url="redis://localhost:6379", max_requests=10000, window_seconds=1):
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis = None

    async def get_redis(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def acquire(self, client_id: str) -> bool:
        """Token bucket implementation using Redis"""
        redis = await self.get_redis()
        current_time = int(time.time())
        key = f"rate_limit:{client_id}:{current_time}"
        
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, self.window_seconds + 2)
            results = await pipe.execute()
            
        requests_in_window = results[0]
        return requests_in_window <= self.max_requests
