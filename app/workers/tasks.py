from app.workers.celery_app import celery_app
from sqlalchemy.orm import Session
from app.models.models import MedicalRecord, Patient
from app.repositories.base import BaseRepository
import ai_service # Preserved logic
import json
from datetime import datetime

@celery_app.task(name="process_medical_document")
def process_medical_document_task(record_id: int, file_path: str, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Business logic remains identical, just wrapped in Celery
        record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
        if not record: return "Fail: No Record"
        
        # 1. OCR + Analysis (Preserved)
        analysis = ai_service.process_medical_document_gemini(file_path)
        
        # 2. Update Record
        record.raw_text = analysis.get("raw_text", "")
        record.ai_extracted = analysis.get("structured_data", {})
        record.ai_summary = analysis.get("patient_summary", "Analyzed.")
        record.patient_summary = analysis.get("patient_summary", "Analyzed.")
        record.doctor_summary = analysis.get("doctor_summary", "")
        record.ai_processed_at = datetime.utcnow()
        
        db.commit()
        return f"Success: Processed record {record_id}"
    finally:
        db.close()
