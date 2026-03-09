import redis
import json
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def set_otp(self, identifier: str, otp: str, expire_seconds: int = 600):
        self.client.setex(f"otp:{identifier}", expire_seconds, otp)

    def get_otp(self, identifier: str) -> str:
        return self.client.get(f"otp:{identifier}")

    def delete_otp(self, identifier: str):
        self.client.delete(f"otp:{identifier}")

    def blacklist_token(self, jti: str, expire_seconds: int):
        self.client.setex(f"blacklist:{jti}", expire_seconds, "true")

    def is_token_blacklisted(self, jti: str) -> bool:
        return self.client.exists(f"blacklist:{jti}") > 0

    def get_rate_limit(self, key: str) -> int:
        val = self.client.get(f"ratelimit:{key}")
        return int(val) if val else 0

    def incr_rate_limit(self, key: str, window: int = 60):
        pipe = self.client.pipeline()
        pipe.incr(f"ratelimit:{key}")
        pipe.expire(f"ratelimit:{key}", window)
        pipe.execute()

redis_service = RedisService()
