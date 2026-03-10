from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Patient, Doctor
from app.repositories.base import UserRepository, PatientRepository

async def get_db_user(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get the full DB User object from the JWT payload."""
    email = current_user.get("sub")
    repo = UserRepository(User, db)
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_patient(user: User = Depends(get_db_user), db: AsyncSession = Depends(get_db)) -> Patient:
    """Dependency to gate routes for patients and return the Patient profile."""
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    
    repo = PatientRepository(Patient, db)
    patient = await repo.get_by_user_id(user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

async def get_current_doctor(user: User = Depends(get_db_user), db: AsyncSession = Depends(get_db)) -> Doctor:
    """Dependency to gate routes for doctors and return the Doctor profile."""
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    
    # Simple lookup for now, can be refactored to Repo
    stmt = select(Doctor).where(Doctor.user_id == user.id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor
