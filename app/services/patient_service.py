from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Patient, User, Condition, Medication
from app.schemas import schemas
from app.core import security
import uuid

class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def setup_profile(self, data: schemas.PatientCreate, user_id: int) -> Patient:
        """Upsert onboarding logic for patients."""
        from sqlalchemy import select
        
        # 1. Check if patient already exists for this user
        stmt = select(Patient).where(Patient.user_id == user_id)
        result = await self.db.execute(stmt)
        patient = result.scalars().first()
        
        if not patient:
            # Create new if not exists (e.g. social login)
            patient = Patient(
                user_id=user_id,
                ahp_id=f"AHP-{uuid.uuid4().hex[:8].upper()}",
                phone_number=data.phone_number,
                language_code=data.language_code
            )
            self.db.add(patient)
            await self.db.flush()
        
        # 2. Update fields
        patient.date_of_birth = data.date_of_birth
        patient.gender = data.gender
        patient.blood_group = data.blood_group
        
        # 3. Handle conditions (Clear and re-add or sync)
        # For simplicity in onboarding, we append or clear
        for c_name in data.conditions:
            cond = Condition(patient_id=patient.id, name=c_name, added_by="patient")
            self.db.add(cond)
            
        # 4. Handle medications
        for m_name in data.medications:
            med = Medication(patient_id=patient.id, generic_name=m_name, added_by="patient")
            self.db.add(med)
            
        await self.db.commit()
        await self.db.refresh(patient)
        return patient
