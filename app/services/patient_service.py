from sqlalchemy.orm import Session
from app.repositories.medical import MedicalRecordRepository
from app.models.models import MedicalRecord
from app.workers.tasks import process_medical_document_task
from app.core.config import settings

class PatientService:
    def __init__(self, db: Session):
        self.db = db
        self.record_repo = MedicalRecordRepository(model=MedicalRecord, db=db)

    def upload_and_process(self, patient_id: int, file_path: str):
        # Create record entry
        record_data = {
            "patient_id": patient_id,
            "type": "document",
            "file_url": file_path, # In reality, s3_url
            "ai_summary": "Queued for processing..."
        }
        record = self.record_repo.create(record_data)
        
        # Offload to Celery
        process_medical_document_task.delay(record.id, file_path, settings.DATABASE_URL)
        return record
