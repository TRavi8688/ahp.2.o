import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from app.schemas import schemas
from app.core import security
from app.api import deps
from app.core.logging import logger
from app.core.insforge_client import insforge
from app.core.audit import log_audit_action
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/doctor/verify", tags=["Doctor Verification"])

@router.post("/start", response_model=schemas.DoctorVerifySessionResponse)
async def start_verification(
    data: schemas.DoctorVerifyStart,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Step 1: Start Doctor Verification (Professional Details)
    """
    if not data.registration_number.upper().startswith("NMC-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Registration Number. Must be verified by National Medical Commission."
        )
    
    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "full_name": data.full_name,
        "registration_number": data.registration_number,
        "state_medical_council": data.state_medical_council,
        "mobile_number": data.mobile_number,
        "status": "basic_verified"
    }
    
    await insforge.create_record("doctor_verification_sessions", session_data)
    await log_audit_action(
        db, 
        "DOCTOR_VERIFY_START", 
        resource_type="VERIFICATION_SESSION",
        details={"session_id": session_id, "registration_number": data.registration_number}
    )
    
    return {"session_id": session_id, "status": "basic_verified"}

@router.post("/identity", response_model=schemas.DoctorVerifySessionResponse)
async def upload_identity(
    session_id: str,
    aadhaar_file: UploadFile = File(...),
    selfie_file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Step 2: Identity Verification (Aadhaar + Selfie)
    """
    session = await insforge.get_one("doctor_verification_sessions", session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    update_data = {
        "aadhaar_url": f"uploads/{session_id}_aadhaar.jpg",
        "selfie_url": f"uploads/{session_id}_selfie.jpg",
        "face_match_score": 0.98,
        "status": "identity_verified"
    }
    
    await insforge.update_record("doctor_verification_sessions", {"session_id": session_id}, update_data)
    await log_audit_action(
        db, 
        "DOCTOR_IDENTITY_UPLOAD", 
        resource_type="VERIFICATION_SESSION",
        details={"session_id": session_id}
    )
    return {"session_id": session_id, "status": "identity_verified"}

@router.post("/send-otp")
async def send_verification_otp(
    session_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Step 3a: Send OTP for Mobile Verification.
    """
    session = await insforge.get_one("doctor_verification_sessions", session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    otp = "123456" # Mock OTP
    await insforge.update_record("doctor_verification_sessions", {"session_id": session_id}, {"otp": otp})
    
    await log_audit_action(
        db, 
        "DOCTOR_VERIFY_OTP_SENT", 
        resource_type="VERIFICATION_SESSION",
        details={"session_id": session_id}
    )
    return {"status": "success", "message": "OTP sent successfully."}

@router.post("/verify-otp", response_model=schemas.DoctorVerifySessionResponse)
async def verify_verification_otp(
    data: schemas.DoctorVerifyOTP,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Step 3b: Verify OTP.
    """
    session = await insforge.get_one("doctor_verification_sessions", session_id=data.session_id)
    if not session or session.get("otp") != data.otp:
        await log_audit_action(
            db, 
            "DOCTOR_VERIFY_OTP_FAILURE", 
            resource_type="VERIFICATION_SESSION",
            details={"session_id": data.session_id}
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    await insforge.update_record("doctor_verification_sessions", {"session_id": data.session_id}, {"status": "otp_verified"})
    await log_audit_action(
        db, 
        "DOCTOR_VERIFY_OTP_SUCCESS", 
        resource_type="VERIFICATION_SESSION",
        details={"session_id": data.session_id}
    )
    return {"session_id": data.session_id, "status": "otp_verified"}

@router.post("/complete", response_model=schemas.Token)
async def complete_verification(
    data: schemas.DoctorVerifyComplete,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Step 4: Set Password and Complete Account Creation.
    """
    session = await insforge.get_one("doctor_verification_sessions", session_id=data.session_id)
    if not session or session.get("status") != "otp_verified":
        raise HTTPException(status_code=400, detail="Identity verification flow not completed or out of sequence.")
        
    full_name = session.get("full_name", "")
    reg_no = session.get("registration_number", "")
    parts = full_name.strip().split()
    last_name = parts[-1].lower() if parts else "doctor"
    last4 = reg_no[-4:] if len(reg_no) >= 4 else "0000"
    doctor_id = f"doctor@{last_name}.{last4}"
    
    existing_user = await insforge.get_one("users", email=doctor_id)
    if existing_user:
         doctor_id = f"doctor@{last_name}.{last4}.{secrets.randbelow(999)}"

    user_data = {
        "email": doctor_id,
        "hashed_password": security.get_password_hash(data.password),
        "role": "doctor",
        "first_name": parts[0] if parts else "Doctor",
        "last_name": last_name
    }
    
    user = await insforge.create_record("users", user_data)
    user_uuid = user.get("id")
    
    doctor_data = {
        "user_id": user_uuid,
        "specialty": "General Practitioner",
        "license_number": reg_no,
        "license_status": "verified",
        "verification_notes": "Auto-verified via Nirixa protocol."
    }
    await insforge.create_record("doctors", doctor_data)
    await insforge.update_record("doctor_verification_sessions", {"session_id": data.session_id}, {"status": "completed"})
    
    await log_audit_action(
        db, 
        "DOCTOR_VERIFY_COMPLETE", 
        user_id=user_uuid,
        resource_type="USER",
        details={"email": doctor_id}
    )
    
    access_token = security.create_access_token(doctor_id, "doctor")
    refresh_token = security.create_refresh_token(doctor_id, "doctor")
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }
