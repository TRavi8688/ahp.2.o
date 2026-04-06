import os
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.core.logging import logger

from typing import Dict, Any, Optional

# --- BILLION-DOLLAR INFRASTRUCTURE: FAILOVER STATE ---
class FailoverManager:
    # Tracks if the primary database is "Down" and for how long
    is_primary_down = False
    last_failure_time = 0
    COOLDOWN_SECONDS = 30 # Wait 30s before trying Primary again after a crash

    @classmethod
    def should_try_primary(cls) -> bool:
        if not cls.is_primary_down:
            return True
        # If cooldown finished, try Primary again
        if time.time() - cls.last_failure_time > cls.COOLDOWN_SECONDS:
            logger.info("FAILOVER_RECOVERY: Attempting to return to Primary Database...")
            return True
        return False

    @classmethod
    def mark_primary_down(cls):
        if not cls.is_primary_down:
            logger.critical("FAILOVER_TRIGGERED: Primary Database is DOWN. Switching to SECONDARY (Railway).")
            cls.is_primary_down = True
        cls.last_failure_time = time.time()

    @classmethod
    def mark_primary_up(cls):
        if cls.is_primary_down:
            logger.info("FAILOVER_RESOLVED: Primary Database is back online.")
            cls.is_primary_down = False

# --- ENGINE CONFIGURATION ---
def create_resilient_engine(url: str):
    if not url: return None
    is_sqlite = "sqlite" in url
    kwargs: Dict[str, Any] = {"echo": False, "pool_pre_ping": True}
    
    if not is_sqlite:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs.update({
            "pool_size": 20,
            "max_overflow": 10,
            "pool_recycle": 3600,
            "pool_timeout": 5, # Fail fast: 5s
            "connect_args": {"ssl": ctx, "command_timeout": 15}
        })
    return create_async_engine(url, **kwargs)

# Initialize both engines
primary_engine = create_resilient_engine(settings.async_database_url)
secondary_engine = create_resilient_engine(os.environ.get("DATABASE_URL_SECONDARY")) if os.environ.get("DATABASE_URL_SECONDARY") else None

# Backward compatibility for existing imports
engine = primary_engine
AsyncSessionLocal = async_sessionmaker(primary_engine, expire_on_commit=False, class_=AsyncSession)

# --- BILLION-DOLLAR DB DEPENDENCY ---
async def get_db():
    """High-Availability DB dependency with millisecond failover."""
    target_engine = primary_engine
    
    # 1. Check if we should even try the primary
    if not FailoverManager.should_try_primary() and secondary_engine:
        target_engine = secondary_engine

    # 2. Attempt Connection
    try:
        if not target_engine:
            raise OperationalError("No engine initialized", None, None)
            
        async with async_sessionmaker(target_engine, expire_on_commit=False, class_=AsyncSession)() as session:
            # Operational Test (The 'Pre-Ping')
            await session.execute(text("SELECT 1"))
            FailoverManager.mark_primary_up() if target_engine == primary_engine else None
            yield session
            
    except (OperationalError, Exception) as e:
        # 3. FAILOVER LOGIC
        if target_engine == primary_engine and secondary_engine:
            FailoverManager.mark_primary_down()
            logger.warning(f"DATABASE_FAILOVER: Primary failed ({str(e)}). Switching to Secondary NOW.")
            
            async with async_sessionmaker(secondary_engine, expire_on_commit=False, class_=AsyncSession)() as session:
                yield session
        else:
            logger.error(f"DATABASE_CRITICAL_FAILURE: All databases unreachable! {str(e)}")
            raise


