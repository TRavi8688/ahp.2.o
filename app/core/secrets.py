import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, default: Any = None) -> Any:
    """
    ENTERPRISE SECRETS RETRIEVAL.
    Strictly enforces retrieval from environment or managed storage.
    Fails fast if a required secret is missing in production.
    """
    # In production, we assume secrets are injected as environment variables
    # (e.g., via AWS Secrets Manager or K8s External Secrets).
    
    value = os.getenv(secret_name)
    
    if value:
        # Logging only the presence, never the value.
        logger.info(f"SECRET_LOADER: Loaded '{secret_name}' successfully.")
        return value
    
    # Fail-fast for production
    if os.getenv("ENVIRONMENT") == "production":
        logger.critical(f"MISSING_MANDATORY_SECRET: '{secret_name}' is required for production.")
        raise RuntimeError(f"CRITICAL ERROR: Mandatory secret '{secret_name}' is missing.")
    
    if default is not None:
        logger.warning(f"SECRET_LOADER: Using default for '{secret_name}'. (Non-Production Only)")
        return default
        
    return None
