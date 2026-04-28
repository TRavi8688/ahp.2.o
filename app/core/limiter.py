from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings
import os

# Enterprise: Distributed Rate Limiting
# Moving window prevents 'edge bursts' allowed by fixed windows.
# Redis is ENFORCED in production to prevent split-brain limits across pods.
env = os.environ.get("ENVIRONMENT", "production").lower()
storage_uri = settings.REDIS_URL if settings.USE_REDIS else "memory://"

if env == "production" and storage_uri == "memory://":
    # Google-grade engineering: Fail fast on unsafe configurations
    raise RuntimeError("CRITICAL: Redis is mandatory for distributed rate limiting in production.")

async def check_ip_blacklist(ip: str) -> bool:
    """Enterprise Breach Containment: Blocks suspicious IPs in Redis."""
    from app.services.redis_service import redis_service
    is_blocked = await redis_service.get(f"blacklist:{ip}")
    return bool(is_blocked)

async def blacklist_ip(ip: str, duration: int = 3600):
    """Automatically blacklists an IP after excessive violations."""
    from app.services.redis_service import redis_service
    await redis_service.set(f"blacklist:{ip}", "BLOCKED", expire=duration)
    logger.warning("IP_BLACKLISTED", ip=ip, duration=duration)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    strategy="moving-window",
    default_limits=["1000 per day", "200 per hour"]
)
