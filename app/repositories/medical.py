from sqlalchemy import select
from app.repositories.base import AsyncBaseRepository
from app.models.models import MedicalRecord, Condition, Medication, Allergy, DoctorAccess, Notification

class MedicalRecordRepository(AsyncBaseRepository):
    async def get_by_patient(self, patient_id: int):
        stmt = select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class ConditionRepository(AsyncBaseRepository):
    async def get_active_by_patient(self, patient_id: int):
        stmt = select(Condition).where(
            Condition.patient_id == patient_id, 
            Condition.hidden_by_patient == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class MedicationRepository(AsyncBaseRepository):
    async def get_active_by_patient(self, patient_id: int):
        stmt = select(Medication).where(
            Medication.patient_id == patient_id, 
            Medication.active == True
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class NotificationRepository(AsyncBaseRepository):
    async def get_unread_by_patient(self, patient_id: int):
        stmt = select(Notification).where(
            Notification.patient_id == patient_id, 
            Notification.read == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
