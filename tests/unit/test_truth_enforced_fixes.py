import asyncio
import uuid
import sys
from fastapi import HTTPException

# Add current dir to path for imports
import os
sys.path.append(os.getcwd())

from app.core.security import create_access_token, create_refresh_token, get_current_user
from app.services.ai_service import AsyncAIService

async def test_token_type_enforcement():
    user_id = str(uuid.uuid4())
    print("\n--- Testing JWT Token Type Enforcement ---")
    
    # 1. Access Token should pass
    access_token = create_access_token(user_id, role="patient")
    # Simulate FastAPI dependency injection
    payload = get_current_user(token=access_token)
    assert payload["type"] == "access"
    print("✅ Access Token: Accepted")
    
    # 2. Refresh Token should fail in get_current_user
    refresh_token = create_refresh_token(user_id, role="patient")
    try:
        get_current_user(token=refresh_token)
        print("❌ Refresh Token: ACCEPETED (FAIL)")
        sys.exit(1)
    except HTTPException as e:
        assert e.status_code == 401
        assert "Access token required" in e.detail
        print("✅ Refresh Token: Rejected (Correct)")

async def test_ai_timeout_reduction():
    print("\n--- Testing AI Service Timeout Configuration ---")
    ai_service = AsyncAIService()
    client = await ai_service.get_client()
    # Check if timeout is 10s
    # httpx.AsyncClient.timeout returns a Timeout object
    if client.timeout.connect == 10.0 and client.timeout.read == 10.0:
        print("✅ AI Service Timeout: 10s (Correct)")
    else:
        print(f"❌ AI Service Timeout: {client.timeout} (Incorrect)")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_token_type_enforcement())
    asyncio.run(test_ai_timeout_reduction())
    print("\n--- ALL TRUTH-ENFORCED FIXES VERIFIED ---")
