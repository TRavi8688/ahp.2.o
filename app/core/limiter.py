from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Enterprise: Distributed Rate Limiting using Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL, # Enable Redis-backed distributed state
    strategy="fixed-window", # Fixed window is most efficient for C1K
)
