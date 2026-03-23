import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger

class CacheService:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        try:
            r = await self.get_redis()
            data = await r.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache Get Error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            r = await self.get_redis()
            await r.set(key, json.dumps(value), ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache Set Error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            r = await self.get_redis()
            await r.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache Delete Error for {key}: {e}")
            return False

    async def close(self):
        if self._redis:
            await self._redis.close()

cache = CacheService()
