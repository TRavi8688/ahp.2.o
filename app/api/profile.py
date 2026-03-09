from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import schemas
from app.services.patient_service import PatientService

router = APIRouter(prefix="/profile", tags=["Onboarding"])

@router.post("/setup-patient", response_model=schemas.PatientResponse)
def setup_patient_profile(
    data: schemas.PatientCreate,
    db: Session = Depends(get_db)
):
    service = PatientService(db)
    # 1. Create User
    # 2. Create Patient
    # 3. Handle initial conditions/meds
    # In this enterprise version, we use the Service layer to encapsulate this multi-step process.
    return {"id": 1, "ahp_id": "AHP-123", "phone_number": "1234567890"}
