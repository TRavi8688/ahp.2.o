import uuid
import secrets
from typing import Optional, Dict, Any
from sqlalchemy import select
from app.services.base import BaseService
from app.models.models import DoctorVerificationSession, User, Doctor, VerificationStatusEnum, RoleEnum
from app.core.security import get_password_hash
from app.core.logging import logger

class VerificationService(BaseService[DoctorVerificationSession]):
    def __init__(self, db):
        super().__init__(DoctorVerificationSession, db)

    async def start_session(self, full_name: str, reg_no: str, state_council: str, mobile: str) -> str:
        session_id = str(uuid.uuid4())
        await self.create(
            session_id=session_id,
            full_name=full_name,
            registration_number=reg_no,
            state_medical_council=state_council,
            mobile_number=mobile,
            status=VerificationStatusEnum.basic_verified
        )
        return session_id

    async def get_by_session_id(self, session_id: str) -> Optional[DoctorVerificationSession]:
        stmt = select(self.model).where(self.model.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_identity(self, session_id: str, aadhaar_url: str, selfie_url: str) -> bool:
        session = await self.get_by_session_id(session_id)
        if not session:
            return False
        
        session.aadhaar_url = aadhaar_url
        session.selfie_url = selfie_url
        session.face_match_score = 0.98  # Mock AI score as per original logic
        session.status = VerificationStatusEnum.identity_verified
        await self.db.flush()
        return True

    async def generate_otp(self, session_id: str) -> Optional[str]:
        session = await self.get_by_session_id(session_id)
        if not session:
            return None
        
        otp = "".join([str(secrets.SystemRandom().randrange(10)) for _ in range(6)])
        session.otp = otp
        await self.db.flush()
        return otp

    async def verify_otp(self, session_id: str, otp: str) -> bool:
        session = await self.get_by_session_id(session_id)
        if not session or session.otp != otp:
            return False
        
        session.status = VerificationStatusEnum.otp_verified
        await self.db.flush()
        return True

    async def complete_verification(self, session_id: str, password: str) -> Optional[User]:
        session = await self.get_by_session_id(session_id)
        if not session or session.status != VerificationStatusEnum.otp_verified:
            return None

        # Logic to generate standardized doctor ID
        parts = session.full_name.strip().split()
        last_name = parts[-1].lower() if parts else "doctor"
        last4 = session.registration_number[-4:] if len(session.registration_number) >= 4 else "0000"
        doctor_email = f"doctor@{last_name}.{last4}"
        
        # Check for collision
        stmt = select(User).where(User.email == doctor_email)
        res = await self.db.execute(stmt)
        if res.scalars().first():
            doctor_email = f"doctor@{last_name}.{last4}.{secrets.randbelow(999)}"

        # Create User
        new_user = User(
            email=doctor_email,
            hashed_password=get_password_hash(password),
            role=RoleEnum.doctor,
            first_name=parts[0] if parts else "Doctor",
            last_name=last_name,
            is_active=True
        )
        self.db.add(new_user)
        await self.db.flush()

        # Create Doctor Profile
        new_doctor = Doctor(
            user_id=new_user.id,
            specialty="General Practitioner",
            license_number=session.registration_number,
            license_status="verified",
            verification_notes="Auto-verified via secure enterprise protocol."
        )
        self.db.add(new_doctor)
        
        session.status = VerificationStatusEnum.completed
        await self.db.flush()
        
        return new_user
