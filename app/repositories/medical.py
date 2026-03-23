from sqlalchemy import select
from app.repositories.base import AsyncBaseRepository
from app.models.models import MedicalRecord, Condition, Medication, Allergy, DoctorAccess, Notification
from app.core.security import calculate_content_checksum
from app.core.logging import logger

class MedicalRecordRepository(AsyncBaseRepository):
    async def get_by_patient(self, patient_id: int):
        stmt = select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())
        
        # Verify integrity of each record
        for record in records:
            if record.record_checksum:
                # We checksum the raw_text or file_url as the 'anchor' for integrity
                expected = calculate_content_checksum(record.raw_text or record.file_url)
                if record.record_checksum != expected:
                     logger.critical(f"TAMPER_DETECTED: Record {record.id} checksum mismatch!")
                     # In a real hardened system, we might raise an error or flag the record
        return records

    async def create_with_integrity(self, obj_in: dict) -> MedicalRecord:
        """Create a record and automatically anchor its integrity with a checksum."""
        # Calculate checksum before saving
        anchor = obj_in.get("raw_text") or obj_in.get("file_url")
        obj_in["record_checksum"] = calculate_content_checksum(anchor)
        
        return await self.create(obj_in)

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
