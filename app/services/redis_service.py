import redis.asyncio as redis
import json
from typing import Optional
from app.core.config import settings

class RedisService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client

    async def set_otp(self, identifier: str, otp: str, expire_seconds: int = 600):
        client = self.get_client()
        await client.setex(f"otp:{identifier}", expire_seconds, otp)

    async def get_otp(self, identifier: str) -> Optional[str]:
        client = self.get_client()
        return await client.get(f"otp:{identifier}")

    async def delete_otp(self, identifier: str):
        client = self.get_client()
        await client.delete(f"otp:{identifier}")

    async def blacklist_token(self, jti: str, expire_seconds: int):
        client = self.get_client()
        await client.setex(f"blacklist:{jti}", expire_seconds, "true")

    async def is_token_blacklisted(self, jti: str) -> bool:
        client = self.get_client()
        return await client.exists(f"blacklist:{jti}") > 0

redis_service = RedisService()
