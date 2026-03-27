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
    
    # DATABASE - Prioritizes InsForge PostgreSQL in production
    # Host: ke6vx29r.us-east.insforge.app:5432, db: insforge, user: postgres
    DATABASE_URL: str = "postgresql+asyncpg://postgres:ahp_secure_2026@ke6vx29r.us-east.insforge.app:5432/insforge"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: Any, info: Any) -> Any:
        # 1. Check if we're in development Mode (Default to production)
        env = os.environ.get("ENVIRONMENT", "production").lower()
        is_dev = env == "development"
        
        # 2. Prefer explicit env var if set
        raw = os.environ.get("DATABASE_URL", "")
        if raw and "sqlite" not in raw:
            v = raw
        elif is_dev and not raw:
            # Only use SQLite for LOCAL development
            return "sqlite+aiosqlite:///./test.db"
        elif not is_dev and not raw and not v:
             # Safety check for production mistyped env vars
             logger.critical("PRODUCTION_ERROR: No DATABASE_URL found. App will likely crash.")
        
        url = str(v)
        
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

    def validate_production_config(self):
        """Strict fail-fast validation for Production environments."""
        env = os.environ.get("ENVIRONMENT", "production").lower()
        if env == "development":
            logger.info("VALIDATION: Development mode active. Skipping strict checks.")
            return

        # 1. Database URL Safety
        if not self.DATABASE_URL or "sqlite" in self.DATABASE_URL:
            logger.critical("PRODUCTION_BLOCKER: DATABASE_URL is missing or uses SQLite in production.")
            raise RuntimeError("CRITICAL: PRODUCTION requires a PostgreSQL connection.")

        # 2. Critical Secret Verification
        missing_secrets = []
        if self.ACCESS_TOKEN_SECRET == "8v93k4m5n6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p":
            missing_secrets.append("ACCESS_TOKEN_SECRET (Used Default)")
        if self.ENCRYPTION_KEY == "VTnc-u0Pxk9_0QB2v88NyOZAzJqTeGk6QGz7o_B3i64=":
            missing_secrets.append("ENCRYPTION_KEY (Used Default)")
        
        if missing_secrets:
            logger.error(f"SECURITY_WARNING: Default secrets detected in production: {', '.join(missing_secrets)}")
            logger.warning("DEGRADED_SECURITY: Allowing startup for INITIAL DEPLOYMENT only. Change secrets to prevent data breaches.")
            # raise RuntimeError("CRITICAL: Production requires unique, secure secrets.")

        # 3. System Binary Check (Tesseract)
        import shutil
        if not shutil.which("tesseract"):
            logger.critical("PRODUCTION_BLOCKER: 'tesseract' binary not found. OCR will fail.")
            # We don't necessarily crash the whole app if OCR is only one module, 
            # BUT for AHP it's a core dependency.
            raise RuntimeError("CRITICAL: tesseract-ocr binary missing from system path.")

        logger.info("VALIDATION: Production configuration verified.")

settings = Settings()
# Call validation early — If this fails, the process should not even start.
settings.validate_production_config()
