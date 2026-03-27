from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Enterprise: Distributed Rate Limiting with Fallback
# If USE_REDIS is False, use in-memory storage to prevent startup hangs
storage_uri = settings.REDIS_URL if settings.USE_REDIS else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    strategy="fixed-window",
)
