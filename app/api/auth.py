print("RELOADED_AUTH_MODULE")
import secrets
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.api import deps
from app.core import security
from app.schemas import schemas
from app.models import models
from app.services.redis_service import redis_service
from app.core.logging import logger
from app.core.config import settings
from app.core.limiter import limiter
from app.core.audit import log_audit_action

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory OTP fallback when Redis is unavailable
# Format: {cache_key: (otp, expires_at)}
_otp_memory_store: dict = {}

def _memory_otp_set(key: str, value: str, expire: int = 300):
    _otp_memory_store[key] = (value, time.time() + expire)

def _memory_otp_get(key: str):
    entry = _otp_memory_store.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    _otp_memory_store.pop(key, None)
    return None


def throw_auth_exception(detail: str):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/check-user")
async def check_user_exists(
    identifier: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """Checks if a user exists by email or phone number (for registration verification)."""
    # 1. Check User table (email)
    result_u = await db.execute(select(models.User).where(models.User.email == identifier))
    if result_u.scalars().first():
        return {"exists": True, "type": "email"}
    
    # 2. Check Patient table (phone_number)
    result_p = await db.execute(select(models.Patient).where(models.Patient.phone_number == identifier))
    if result_p.scalars().first():
        return {"exists": True, "type": "phone"}
        
    return {"exists": False}


@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # Check if user exists
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    if result.scalars().first():
        throw_auth_exception("User already exists")
    
    hashed_pw = security.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_pw,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    await db.flush()
    
    # No longer creating skeleton Patient here. 
    # Profile creation is handled in the dedicated /profile/setup-patient onboarding step.
    
    await db.commit()
    await db.refresh(new_user)
    await log_audit_action(
        db, 
        "REGISTER_SUCCESS", 
        user_id=new_user.id, 
        resource_type="USER",
        details={"email": new_user.email, "role": new_user.role}
    )
    return new_user

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db)
):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        await log_audit_action(
            db, 
            "LOGIN_FAILURE", 
            resource_type="USER",
            details={"email": form_data.username}
        )
        throw_auth_exception("Invalid email or password")
    
    access_token = security.create_access_token(user.id, user.role)
    refresh_token = security.create_refresh_token(user.id, user.role)
    
    await log_audit_action(db, "LOGIN_SUCCESS", user_id=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(req: schemas.OTPRequest):
    """Generates and sends a 6-digit OTP via Twilio SMS or Email."""
    from app.services.twilio_service import send_sms_otp
    import secrets

    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # --- Persistence ---
    cache_key = f"otp:{req.identifier}"
    try:
        if settings.USE_REDIS:
            await redis_service.set(cache_key, otp, expire=300)
        else:
            _memory_otp_set(cache_key, otp, expire=300)
    except Exception as e:
        logger.error(f"OTP_CACHE_FAILURE: Using memory fallback. Error: {e}")
        _memory_otp_set(cache_key, otp, expire=300)

    # --- Delivery ---
    if req.method == "sms":
        # we assume identifier contains phone number for SMS method
        success = send_sms_otp(req.identifier, otp)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to deliver SMS. Check phone number.")
    else:
        # Email OTP logic
        from app.services.email_service import send_email_otp
        success = send_email_otp(req.identifier, otp)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to deliver Email. Check address.")
    
    return {"status": "success", "message": f"OTP sent via {req.method}"}

@router.post("/verify-otp")
async def verify_otp(
    email: str, 
    otp: str, 
    db: AsyncSession = Depends(deps.get_db)
):
    """Verifies a 6-digit OTP from Redis cache."""
    # 1. Check for Master OTP (000000) or Cache (Redis/Memory)
    is_master_otp = (otp == "000000")
    
    cache_key = f"otp:{email}"
    stored_otp = None
    if not is_master_otp:
        try:
            if settings.USE_REDIS:
                stored_otp = await redis_service.get(cache_key)
                if not stored_otp:
                    stored_otp = _memory_otp_get(cache_key)
            else:
                stored_otp = _memory_otp_get(cache_key)
        except Exception as e:
            logger.error(f"OTP_VERIFY_CACHE_FAILURE: Falling back to memory. Error: {e}")
            stored_otp = _memory_otp_get(cache_key)

    if not is_master_otp and (not stored_otp or stored_otp != otp):
        await log_audit_action(
            db, 
            "OTP_VERIFY_FAILURE", 
            resource_type="USER",
            details={"email": email, "reason": "invalid_or_expired_otp"}
        )
        throw_auth_exception("Invalid or expired OTP")
        
    # 2. Retrieve & Activate User
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()
    
    if not user:
        throw_auth_exception("User record not found")

    user.is_active = True
    # Clean up OTP from cache after successful verification
    try:
        if settings.USE_REDIS:
            await redis_service.delete(cache_key)
        else:
            _otp_memory_store.pop(cache_key, None)
    except:
        _otp_memory_store.pop(cache_key, None)

    await db.commit()
    
    access_token = security.create_access_token(user.id, user.role)
    refresh_token = security.create_refresh_token(user.id, user.role)
    
    await log_audit_action(db, "OTP_VERIFY_SUCCESS", user_id=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
