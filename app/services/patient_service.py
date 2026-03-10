from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Patient, User, Condition, Medication
from app.schemas import schemas
from app.core import security
import uuid

class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def setup_profile(self, data: schemas.PatientCreate) -> Patient:
        """High-level onboarding logic for patients."""
        # 1. Logic already partially in auth.py, but this is the full version
        # Check if user exists (should ideally be handled by auth/onboarding bridge)
        # This is for the POST /setup-patient flow
        
        # Simplified: Create patient if not exists
        patient = Patient(
            ahp_id=f"AHP-{uuid.uuid4().hex[:8].upper()}",
            phone_number=data.phone_number,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_group=data.blood_group,
            language_code=data.language_code
        )
        self.db.add(patient)
        await self.db.flush()
        
        # Add initial conditions
        for c_name in data.conditions:
            cond = Condition(patient_id=patient.id, name=c_name, added_by="patient")
            self.db.add(cond)
            
        # Add initial medications
        for m_name in data.medications:
            med = Medication(patient_id=patient.id, generic_name=m_name, added_by="patient")
            self.db.add(med)
            
        await self.db.commit()
        await self.db.refresh(patient)
        return patient
