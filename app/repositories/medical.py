from app.repositories.base import BaseRepository
from app.models.models import MedicalRecord, Condition, Medication, Allergy, DoctorAccess, Notification

class MedicalRecordRepository(BaseRepository):
    def get_by_patient(self, patient_id: int):
        return self.db.query(self.model).filter(self.model.patient_id == patient_id).all()

class ConditionRepository(BaseRepository):
    def get_active_by_patient(self, patient_id: int):
        return self.db.query(self.model).filter(self.model.patient_id == patient_id, self.model.hidden_by_patient == False).all()

class MedicationRepository(BaseRepository):
    def get_active_by_patient(self, patient_id: int):
        return self.db.query(self.model).filter(self.model.patient_id == patient_id, self.model.active == True).all()

class NotificationRepository(BaseRepository):
    def get_unread_by_patient(self, patient_id: int):
        return self.db.query(self.model).filter(self.model.patient_id == patient_id, self.model.read == False).all()
