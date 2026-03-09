from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.schemas import schemas
from app.repositories.base import UserRepository
from app.services.redis_service import redis_service
from app.core.logging import logger
import random

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_otp(req: schemas.OTPRequest):
    phone = req.identifier.strip().replace(" ", "").replace("-", "")
    otp = str(random.randint(100000, 999999))
    
    # Store in REDIS instead of Dict
    redis_service.set_otp(phone, otp)
    
    logger.info("OTP sent", identifier=phone, otp=otp if settings.DEBUG else "****")
    # Twilio logic would go here
    return {"status": "success", "message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=schemas.Token)
def verify_otp(req: schemas.OTPVerify, db: Session = Depends(get_db)):
    phone = req.identifier.strip().replace(" ", "").replace("-", "")
    stored_otp = redis_service.get_otp(phone)
    
    if not stored_otp or stored_otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    redis_service.delete_otp(phone)
    
    user_repo = UserRepository(model=schemas.UserResponse, db=db) # Note: fix repo init
    user = db.query(UserRepository.model).filter(UserRepository.model.email == phone).first() # Simplified for draft
    
    role = "patient" # Default
    if user:
        role = user.role
    else:
        # Create user if new? Or handle in profile setup? (AHP logic: if new, is_new=True)
        # For brevity, let's assume we handle new user in next step
        pass
        
    access_token = security.create_access_token(phone, role)
    refresh_token = security.create_refresh_token(phone, role)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
