import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.append(os.getcwd())

# Mock environment to satisfy Pydantic required fields
os.environ["ENVIRONMENT"] = "production"
os.environ["DATABASE_URL"] = "postgresql://remote-db/db"
os.environ["REDIS_URL"] = "redis://remote-redis:6379/0"
os.environ["JWT_PRIVATE_KEY"] = "-----BEGIN RSA PRIVATE KEY-----\nValid format\n-----END RSA PRIVATE KEY-----"
os.environ["JWT_PUBLIC_KEY"] = "Valid Public Key"
os.environ["S3_BUCKET_NAME"] = "secure-medical-vault"
os.environ["ENCRYPTION_KEY"] = "a" * 32

def test_config_lockdown():
    """Verify that production mode rejects insecure DB/Auth setups."""
    from app.core.config import Settings
    print("\n[CHECK] Testing Production Config Lockdown...")
    
    # 1. Test localhost DB rejection
    try:
        # Override just the DB URL to be insecure
        Settings(DATABASE_URL="postgresql://localhost/db")
        print("[FAILURE] Production mode accepted insecure localhost DB!")
    except ValueError as e:
        print(f"[SUCCESS] Production mode rejected insecure DB: {e}")

    # 2. Test weak JWT Key rejection
    try:
        # Override just the JWT key to be weak
        Settings(JWT_PRIVATE_KEY="too-weak")
        print("[FAILURE] Production mode accepted weak JWT Private Key!")
    except ValueError as e:
        print(f"[SUCCESS] Production mode rejected weak JWT Key: {e}")

async def test_s3_private_by_default():
    """Verify S3 service returns keys, not public URLs."""
    from app.services.s3_service import StorageService
    
    with patch('boto3.client') as mock_s3:
        service = StorageService()
        key = await service.upload_bytes(b"test", "secret.pdf")
        print(f"[CHECK] S3 Upload Return: {key}")
        if "http" in key:
            print("[FAILURE] S3 returned a public URL!")
            return
        print("[SUCCESS] S3 returned a private object key (no URL leakage).")

if __name__ == "__main__":
    print("\n--- STARTING ZERO-TRUST INTEGRITY AUDIT ---")
    test_config_lockdown()
    asyncio.run(test_s3_private_by_default())
    print("--- AUDIT COMPLETE ---\n")
