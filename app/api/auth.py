import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core import security
from app.schemas import schemas
from app.models.models import User, Patient
from app.services.redis_service import redis_service
from app.core.logging import logger
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Placeholder for registration logic
    # This endpoint was added as per the instruction to apply rate limits.
    # Actual registration logic would go here, e.g., creating a new user in the DB.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Registration endpoint not fully implemented yet.")

@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    user_data: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
):
    # Placeholder for login logic
    # This endpoint was added as per the instruction to apply rate limits.
    # Actual login logic would go here, e.g., authenticating user and returning tokens.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Login endpoint not fully implemented yet.")

@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(req: schemas.OTPRequest):
    """Async OTP dispatch with Redis persistence."""
    phone = req.identifier.strip().replace(" ", "").replace("-", "")
    # Generate a secure OTP (using simple random for now as per requirements)
    otp = str(random.randint(100000, 999999))
    
    # Persist to Async Redis
    await redis_service.set_otp(phone, otp)
    
    logger.info(f"OTP generated for {phone}: {otp if settings.DATABASE_URL == 'debug' else '****'}")
    
    # In a real enterprise app, we'd trigger an async Twilio task here.
    return {"status": "success", "message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=schemas.Token)
async def verify_otp(req: schemas.OTPVerify, db: AsyncSession = Depends(get_db)):
    """Async OTP verification and JWT issuance."""
    phone = req.identifier.strip().replace(" ", "").replace("-", "")
    stored_otp = await redis_service.get_otp(phone)
    
    if not stored_otp or stored_otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    await redis_service.delete_otp(phone)
    
    # Check if user exists
    stmt = select(User).where(User.email == phone) # Using phone as identifier/email for this flow
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    role = "patient"
    if not user:
        # Auto-provision user for AHP 2.0 flow
        user = User(
            email=phone,
            hashed_password=security.get_password_hash(str(uuid.uuid4())),
            role="patient",
            first_name="New",
            last_name="AHP User",
            is_active=True
        )
        db.add(user)
        await db.flush() # Get user ID
        
        # Create Patient Profile
        patient = Patient(
            user_id=user.id,
            ahp_id=f"AHP-{random.randint(10000, 99999)}",
            phone_number=phone,
            language_code="en"
        )
        db.add(patient)
        await db.commit()
    else:
        role = user.role
        
    access_token = security.create_access_token(phone, role)
    refresh_token = security.create_refresh_token(phone, role)
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

import uuid # Added missing import
