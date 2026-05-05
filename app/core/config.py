import os
import logging
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Any
from dotenv import load_dotenv

# Production-grade configuration loader
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AHP 2.0 Secure"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str # Mandatory: production, staging, development
    
    # --- 1. ENTERPRISE AUTHENTICATION (RS256) ---
    # No symmetric secrets allowed for JWT. 
    # Must be PEM-formatted RSA keys.
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    JWT_AUDIENCE: str = "ahp-enterprise-clients"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # --- 2. DATA INTEGRITY ---
    DATABASE_URL: str
    REDIS_URL: str
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: Any) -> str:
        if not v:
            raise ValueError("CRITICAL: DATABASE_URL is mandatory.")
        url = str(v)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # --- 3. INFRASTRUCTURE & COMPLIANCE ---
    ALLOWED_ORIGINS: List[str] = []
    S3_BUCKET_NAME: str
    
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
    
    # --- 4. SECURE COMMUNICATIONS ---
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    
    # --- 5. AI ENGINE (Multi-Provider) ---
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    SARVAM_KEY: Optional[str] = None

    # --- 6. FIELD-LEVEL ENCRYPTION ---
    ENCRYPTION_KEY: str
    PREVIOUS_ENCRYPTION_KEYS: List[str] = []
    
    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_lockdown(self) -> "Settings":
        """Fail-fast check for zero-trust compliance."""
        if self.ENVIRONMENT == "production":
            # 1. Database isolation
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                raise ValueError("PRODUCTION_FAIL: Loopback database detected.")
            
            # 2. Redis isolation
            if not self.REDIS_URL or "localhost" in self.REDIS_URL:
                raise ValueError("PRODUCTION_FAIL: Distributed Redis is mandatory.")
            
            # 3. Auth Integrity
            if "-----BEGIN RSA PRIVATE KEY-----" not in self.JWT_PRIVATE_KEY:
                raise ValueError("PRODUCTION_FAIL: JWT_PRIVATE_KEY must be a valid RSA PEM.")
            
            # 4. Storage Integrity
            if not self.S3_BUCKET_NAME:
                raise ValueError("PRODUCTION_FAIL: S3_BUCKET_NAME is mandatory.")

            # 5. Twilio Integrity
            if not all([self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN, self.TWILIO_FROM_NUMBER]):
                raise ValueError("PRODUCTION_FAIL: Twilio communications must be configured.")
        
        return self

settings = Settings()
