import redis.asyncio as redis
import json
import os
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class RedisService:
    """
    Production-Grade Redis Service.
    NO IN-MEMORY FALLBACKS. This service enforces distributed state consistency.
    If Redis is unavailable, the system fails fast to prevent split-brain scenarios.
    """
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self.redis_url = settings.REDIS_URL

    def get_client(self) -> redis.Redis:
        if self._client is None:
            if not self.redis_url:
                logger.critical("REDIS_CONFIG_MISSING: REDIS_URL must be set in production.")
                raise RuntimeError("CRITICAL: Redis configuration missing.")
            
            self._client = redis.from_url(
                self.redis_url, 
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
        return self._client

    async def set(self, key: str, value: str, expire: int = 600):
        """Standard Redis SETEX operation."""
        client = self.get_client()
        await client.setex(key, expire, value)

    async def get(self, key: str) -> Optional[str]:
        """Standard Redis GET operation."""
        client = self.get_client()
        try:
            return await client.get(key)
        except Exception as e:
            logger.error("REDIS_GET_FAILURE", key=key, error=str(e))
            raise # Fail-fast

    async def delete(self, key: str):
        """Standard Redis DEL operation."""
        client = self.get_client()
        await client.delete(key)

    async def set_nx(self, key: str, value: str, expire: int = 30) -> bool:
        """Atomic SET if Not Exists for distributed locking."""
        client = self.get_client()
        return await client.set(key, value, ex=expire, nx=True)

    async def set_otp(self, identifier: str, otp: str, expire_seconds: int = 600):
        await self.set(f"otp:{identifier}", otp, expire_seconds)

    async def get_otp(self, identifier: str) -> Optional[str]:
        return await self.get(f"otp:{identifier}")

    async def delete_otp(self, identifier: str):
        await self.delete(f"otp:{identifier}")

    async def blacklist_token(self, jti: str, expire_seconds: int):
        await self.set(f"blacklist:{jti}", "true", expire_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        val = await self.get(f"blacklist:{jti}")
        return val == "true"

redis_service = RedisService()
