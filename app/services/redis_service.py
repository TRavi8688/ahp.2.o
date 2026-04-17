import redis.asyncio as redis
import json
import os
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class RedisService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        # Mock store for local 'DEMO_MODE' without Redis
        self._mock_store: Dict[str, Any] = {}
        self.is_demo = os.getenv("DEMO_MODE", "False") == "True"

    def get_client(self) -> redis.Redis:
        if self._client is None:
            try:
                self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning(f"REDIS_CONNECTION_FAILURE: {e}. Falling back to In-Memory store for this session.")
                self.is_demo = True # Force memory mode for survival
        return self._client

    async def set(self, key: str, value: str, expire: int = 600):
        """Unified setter for Demo-Aware Persistence."""
        if self.is_demo:
            self._mock_store[key] = value
            return
        client = self.get_client()
        await client.setex(key, expire, value)

    async def get(self, key: str) -> Optional[str]:
        """Unified getter for Demo-Aware Persistence."""
        if self.is_demo:
            return self._mock_store.get(key)
        client = self.get_client()
        return await client.get(key)

    async def delete(self, key: str):
        """Unified deleter for Demo-Aware Persistence."""
        if self.is_demo:
            self._mock_store.pop(key, None)
            return
        client = self.get_client()
        await client.delete(key)

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
