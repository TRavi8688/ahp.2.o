from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AHP 2.0 Enterprise"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # DATABASE
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ahp_db"
    
    # REDIS
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CELERY
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # External Services
    INSFORGE_URL: Optional[str] = None
    INSFORGE_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = "ahp-records"
    
    # AI Keys
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    SARVAM_KEY: Optional[str] = None
    ENCRYPTION_KEY: str = "g_oKz_1c5uO8j3HlTzQZ8U0sC9p7L5vY6e3JmN1tWgE="
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
