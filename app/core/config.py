import os
import logging
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Any
from dotenv import load_dotenv

# Production-grade configuration loader
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AHP 2.0"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    
    # 1. SECURITY LOCKDOWN: No defaults for critical secrets
    SECRET_KEY: str
    ACCESS_TOKEN_SECRET: str
    REFRESH_TOKEN_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 2. DATA INTEGRITY: Strict single DB source
    DATABASE_URL: str
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: Any) -> str:
        if not v:
            raise ValueError("CRITICAL: DATABASE_URL is mandatory for production.")
        url = str(v)
        # Standardize PostgreSQL async scheme
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # 3. RELIABILITY: Mandatory Redis for Distributed Logic
    REDIS_URL: str
    USE_REDIS: bool = True
    
    # 4. COMPLIANCE: Infrastructure Hardening
    ALLOWED_ORIGINS: List[str] = []
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [i.strip() for i in v.split(",")]
        return v
    
    # 5. EXTERNAL DISCOVERY: Purged InsForge
    S3_BUCKET_NAME: str = "ahp-clinical-vault"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    
    # 6. AI ENGINE: Multi-Provider (No Cloud Backbone)
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    SARVAM_KEY: Optional[str] = None
    
    # 7. ENCRYPTION: Mandatory AEAD
    ENCRYPTION_KEY: str
    PREVIOUS_ENCRYPTION_KEYS: List[str] = []
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    def validate_production_readiness(self):
        """Fail-fast check for production security requirements."""
        if self.ENVIRONMENT == "production":
            if "localhost" in self.DATABASE_URL:
                raise RuntimeError("PRODUCTION_FAIL: Localhost database detected in production mode.")
            if self.SECRET_KEY == "debug_key":
                raise RuntimeError("PRODUCTION_FAIL: Insecure SECRET_KEY used in production.")
            if not self.REDIS_URL:
                raise RuntimeError("PRODUCTION_FAIL: Redis is mandatory for enterprise concurrency.")

settings = Settings()
settings.validate_production_readiness()
