import os
import logging
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Any
from dotenv import load_dotenv

# Basic configuration-level logger to avoid circularity with app.core.logging
logger = logging.getLogger("config")
logging.basicConfig(level=logging.INFO)

# Load .env file at the very beginning of the process
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AHP 2.0 Secure"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    ACCESS_TOKEN_SECRET: str = "8v93k4m5n6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p"
    REFRESH_TOKEN_SECRET: str = "p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # DATABASE - Falls back to InsForge PostgreSQL if DATABASE_URL not explicitly set
    # The InsForge DB host is: ke6vx29r.us-east.insforge.app:5432, db: insforge, user: postgres
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: Any, info: Any) -> Any:
        """Prioritize explicitly set DATABASE_URL env var. 
        Handles common Railway/Docker issues like unexpanded bash vars."""
        raw = os.environ.get("DATABASE_URL", "")
        url = raw if (raw and "sqlite" not in raw) else v
        
        if not url or "sqlite" in str(url):
            return url or "sqlite+aiosqlite:///./test.db"
        
        # Detect unexpanded bash/shell variables like ${DB_PORT}, ${DB_HOST} etc.
        import re
        if re.search(r'\$\{?\w+\}?', str(url)):
            logger.critical(f"DATABASE_URL contains unexpanded shell variables! URL: {url[:50]}...")
            logger.critical("Set DATABASE_URL to the FULL URL with actual values, not variable references.")
            # Fall back to SQLite so the app at least starts
            return "sqlite+aiosqlite:///./test.db"
        
        # Fix common Railway scheme: postgres:// -> postgresql+asyncpg://
        url = str(url)
        
        # Railway adds ?sslmode=disable which breaks asyncpg. Strip it.
        if "?" in url and "sslmode" in url:
            url = url.split("?")[0]
            
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url
    
    # REDIS / CACHE
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False
    
    # CORS
    ALLOWED_ORIGINS: Any = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",")]
        return v
    
    # External Services - InsForge defaults pre-configured
    INSFORGE_BASE_URL: Optional[str] = "https://ke6vx29r.us-east.insforge.app"
    INSFORGE_ANON_KEY: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTU2NzgtOTBhYi1jZGVmMTIzNDU2NzgiLCJlbWFpbCI6ImFub25AaW5zZm9yZ2UuY29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxNzExMzR9.KcxEnpWCr-HUXxtZGfaoX2Cdvi4bbHFZNa_ajGV96wg"
    S3_BUCKET_NAME: str = "medical-reports"
    
    # AI & Encryption
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    SARVAM_KEY: Optional[str] = None
    ENCRYPTION_KEY: str = "VTnc-u0Pxk9_0QB2v88NyOZAzJqTeGk6QGz7o_B3i64="
    DEMO_MODE: bool = False
    
    @property
    def sync_database_url(self) -> str:
        """Standard SQLAlchemy URL with Scheme Fix for migrations."""
        url = self.DATABASE_URL
        if not url or not isinstance(url, str): return ""
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # Strip async drivers for sync use
        if "postgresql+asyncpg://" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if "sqlite+aiosqlite://" in url:
            url = url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url

    @property
    def async_database_url(self) -> str:
        """SQLAlchemy URL for async drivers."""
        url = self.sync_database_url
        if not url: return ""
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and "+aiosqlite" not in url:
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra="ignore"
    )

    def validate_secrets(self):
        """Warn or Fail for missing secrets."""
        # For local SQLite development, we allow some leniency
        if "sqlite" in self.DATABASE_URL:
            logger.info("SQLITE_DETECTED: Skipping strict production secret validation.")
            return

        critical_secrets = [
            ("ACCESS_TOKEN_SECRET", self.ACCESS_TOKEN_SECRET),
            ("REFRESH_TOKEN_SECRET", self.REFRESH_TOKEN_SECRET),
            ("ENCRYPTION_KEY", self.ENCRYPTION_KEY),
            ("DATABASE_URL", self.DATABASE_URL)
        ]
        
        for name, value in critical_secrets:
            if not value or (name != "DATABASE_URL" and len(value) < 16):
                 # Log but don't crash the boot process immediately. 
                 # The individual services will fail when called.
                 logger.critical(f"DEPLOYMENT_ERROR: {name} is MISSING or INVALID in environment.")

settings = Settings()
# Call validation but don't crash the main process directly here
# Individual components like Encryption/Auth will fail-safe when called.
settings.validate_secrets()
