from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Patient, Doctor
from app.repositories.base import UserRepository, PatientRepository
import logging

logger = logging.getLogger(__name__)

async def get_db_user(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
    """
    Standard Enterprise Dependency to retrieve the full User model from JWT.
    Enforces integer-based primary keys for consistent relational integrity.
    """
    user_id_raw = current_user.get("sub")
    
    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        logger.error(f"AUTH_IDENTITY_ERROR: Expected integer sub claim, got {user_id_raw}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identity claim in token."
        )

    repo = UserRepository(User, db)
    user = await repo.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")
    return user

async def get_current_patient(user: User = Depends(get_db_user), db: AsyncSession = Depends(get_db)) -> Patient:
    """Gated dependency for Patient-only routes."""
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Route requires Patient role.")
    
    repo = PatientRepository(Patient, db)
    patient = await repo.get_by_user_id(user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not initialized.")
    return patient

async def get_current_doctor(user: User = Depends(get_db_user), db: AsyncSession = Depends(get_db)) -> Doctor:
    """Gated dependency for Doctor-only routes."""
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Route requires Doctor role.")
    
    stmt = select(Doctor).where(Doctor.user_id == user.id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")
    return doctor
