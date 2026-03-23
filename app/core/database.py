from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Detect database type for correct pooling configuration
_is_sqlite = "sqlite" in settings.async_database_url

# Build engine kwargs — SQLite does NOT support pool_size/max_overflow
_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if not _is_sqlite:
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_recycle"] = 300  # Recycle stale connections every 5 min
    _engine_kwargs["connect_args"] = {"ssl": ctx, "command_timeout": 60, "server_settings": {"search_path": "public"}}
    # Removed invalid prepared_statement_cache_size kwarg

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
    """Dependency for providing an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
