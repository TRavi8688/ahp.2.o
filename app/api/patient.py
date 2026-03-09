from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.base import PatientRepository
from app.models.models import MedicalRecord
from app.workers.tasks import process_medical_document_task
from app.core.config import settings

router = APIRouter(prefix="/patient", tags=["Patient"])

@router.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user = Depends(...) # Integration pending
):
    # 1. Save File to local/S3 (Preserved logic)
    # 2. Create Record in DB
    record = MedicalRecord(
        patient_id=1, # Mock for now
        type="document",
        file_url="temp_url",
        ai_summary="Analyzing..."
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 3. Offload to CELERY (Distributed Scalability)
    process_medical_document_task.delay(record.id, "local_path", settings.DATABASE_URL)
    
    return {"status": "processing", "record_id": record.id}
