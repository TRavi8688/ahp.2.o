from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.schemas import schemas
from app.models.models import Doctor, User
from app.api.deps import get_current_doctor

router = APIRouter(prefix="/doctor", tags=["Doctor"])

@router.get("/profile", response_model=schemas.DoctorResponse)
async def get_doctor_profile(
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """Securely fetch the authenticated doctor's profile."""
    return current_doctor

@router.get("/patients")
async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """List patients that this doctor has clinical access to."""
    # This would involve querying the DoctorAccess table
    # For now, returning empty list as placeholders are replaced with real identity checks
    return []

@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """Doctor-specific health analytics."""
    return {"total_patients": 0, "alerts": []}
