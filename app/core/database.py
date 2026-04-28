import os
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.core.logging import logger

from typing import Dict, Any, Optional

# --- ENGINE CONFIGURATION ---
def create_resilient_engine(url: str):
    if not url: return None
    is_sqlite = "sqlite" in url
    kwargs: Dict[str, Any] = {"echo": False}
    
    if not is_sqlite:
        import ssl
        ctx = ssl.create_default_context()
        # In production, we MUST verify the certificate.
        # If using self-signed certs (e.g. some internal DBs), the CA cert should be added to the system trust store.
        if os.environ.get("ENVIRONMENT") == "development":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        
        kwargs.update({
            "pool_size": 20,
            "max_overflow": 10,
            "pool_recycle": 3600,
            "pool_timeout": 30,
            "pool_pre_ping": True,
            "connect_args": {"ssl": ctx, "command_timeout": 15}
        })
    else:
        kwargs.update({
            "connect_args": {"check_same_thread": False}
        })
    return create_async_engine(url, **kwargs)

# Initialize Primary Engine
primary_engine = create_resilient_engine(settings.async_database_url)
AsyncSessionLocal = async_sessionmaker(primary_engine, expire_on_commit=False, class_=AsyncSession)

# --- ENTERPRISE DB DEPENDENCY ---
async def get_db():
    """
    Standard FastAPI dependency for database sessions.
    ENFORCES EXPLICIT TRANSACTIONS: No auto-committing. 
    Developer MUST call await session.commit() or await session.flush().
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
