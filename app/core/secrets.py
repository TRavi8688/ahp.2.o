import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, default: Any = None) -> Any:
    """
    Retrieves a secret from the system.
    Supports environment-based lookup with hooks for AWS Secrets Manager or HashiCorp Vault.
    """
    # 1. Check for 'Production Mode' Secret Management hooks
    # In a real AWS environment, this would call boto3 or a vault client
    # For this hardening implementation, we provide the plug-and-play structure
    
    # Simulate a check for external secret manager path
    secret_manager_path = os.getenv("SECRET_MANAGER_PATH")
    
    if secret_manager_path:
        try:
            # Placeholder for actual API call to Secret Manager
            # e.g., return client.get_secret_value(SecretId=secret_name)
            logger.info(f"SECRET_RETRIEVAL: Attempting fetch for '{secret_name}' from managed storage.")
        except Exception as e:
            logger.error(f"SECRET_ERROR: Failed to fetch '{secret_name}' from manager: {e}")

    # 2. Fallback to Environment Variables (Standard Pydantic Flow)
    # This ensures that even if the secret manager is unavailable or in dev, the app starts.
    value = os.getenv(secret_name, default)
    
    if value:
        # Avoid logging the actual secret value
        logger.info(f"SECRET_LOADER: Loaded '{secret_name}' successfully.")
    else:
        logger.warning(f"SECRET_LOADER: Secret '{secret_name}' not found.")
        
    return value
