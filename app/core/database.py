from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.core.logging import logger

from typing import Dict, Any

# Detect database type for correct pooling configuration
_is_sqlite = "sqlite" in settings.async_database_url

# Build engine kwargs — Explicitly typed to allow diverse pooling options
_engine_kwargs: Dict[str, Any] = {
    "echo": False,
    "pool_pre_ping": True,
}
if not _is_sqlite:
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    _engine_kwargs["pool_size"] = 50 # Optimized for C1K cluster scaling
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_recycle"] = 300  
    _engine_kwargs["pool_timeout"] = 5 # Fail fast: 5s timeout instead of 10s
    _engine_kwargs["connect_args"] = {
        "ssl": ctx, 
        "command_timeout": 30, # Shorter timeout for better responsiveness
        "server_settings": {"search_path": "public"}
    }

# Enterprise-grade async database engine
engine = create_async_engine(
    settings.async_database_url,
    **_engine_kwargs
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db():
    """Enterprise-grade DB dependency with fail-fast operational error handling."""
    async with AsyncSessionLocal() as session:
        try:
            # Operational check on every request (via pool_pre_ping inside engine)
            yield session
        except OperationalError as e:
            logger.critical("DATABASE_OFFLINE: Could not connect to PostgreSQL.", error=str(e))
            raise
        except Exception as e:
            logger.error(f"DATABASE_ERROR: {str(e)}")
            raise
        finally:
            await session.close()
