import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import MedicalRecord, Patient
from app.workers.tasks import process_medical_document_task
from app.core.config import settings
from app.services.dashboard_service import DashboardService
from app.api.deps import get_current_patient
from app.core.limiter import limiter

router = APIRouter(prefix="/patient", tags=["Patient"])

@router.post("/upload-report")
@limiter.limit("5/minute")
async def upload_report(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient)
):
    """Secure upload report endpoint tied to the authenticated patient."""
    # 1. Save File (Local storage for MVP, S3 in prod)
    file_id = str(uuid.uuid4())
    upload_dir = "uploads/reports"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file_id}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")

    # 2. Persist Record Metadata in DB
    record = MedicalRecord(
        patient_id=current_patient.id,  # SECURE: Tied to real identity
        type="document",
        file_url=file_path,
        ai_summary="Analyzing your report..."
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    # 3. Offload Heavy Processing to Celery
    process_medical_document_task.delay(record.id, file_path)
    
    return {
        "status": "success", 
        "message": "Report uploaded successfully. Analysis is in progress.",
        "record_id": record.id
    }

@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(get_current_patient)
):
    """Secure async dashboard endpoint for the logged-in patient."""
    service = DashboardService(db)
    data = await service.get_dashboard(patient_id=current_patient.id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data
