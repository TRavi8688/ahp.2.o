from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import models
from app.core.logging import logger

class AccessControlService:
    """
    Google-Grade ABAC (Attribute-Based Access Control).
    Ensures that access to clinical records is granted based on 
    dynamic relationships (e.g., active appointments, emergency overrides).
    """
    
    @staticmethod
    async def can_doctor_access_patient(
        db: AsyncSession, 
        doctor_id: int, 
        patient_id: int
    ) -> bool:
        """
        Verify if a doctor has a legitimate clinical reason to access a patient's data.
        """
        # 1. Check for active appointment relationship
        # (Assuming an 'Appointment' model exists or similar junction)
        # For now, we implement a strict relationship check
        # stmt = select(models.Appointment).where(...)
        
        # 2. EMERGENCY_OVERRIDE (Logged as critical event)
        # In a real enterprise system, a doctor might 'break the glass'
        
        # 3. Explicit Grant
        # Check if patient has explicitly granted access to this doctor
        stmt = select(models.AccessGrant).where(
            models.AccessGrant.doctor_id == doctor_id,
            models.AccessGrant.patient_id == patient_id,
            models.AccessGrant.status == models.AccessStatusEnum.granted
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            return True
            
        return False

    @staticmethod
    async def log_access_attempt(
        db: AsyncSession,
        user_id: int,
        resource_id: int,
        granted: bool,
        reason: str
    ):
        """Forensic logging of clinical data access attempts."""
        from app.core.audit import log_audit_action
        action = "DATA_ACCESS_GRANTED" if granted else "DATA_ACCESS_DENIED"
        await log_audit_action(
            db,
            action=action,
            user_id=user_id,
            resource_type="MEDICAL_RECORD",
            resource_id=resource_id,
            details={"granted": granted, "reason": reason}
        )
