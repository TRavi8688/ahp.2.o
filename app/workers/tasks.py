import asyncio
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.models.models import MedicalRecord
from app.services.ai_service import ai_service
from app.services.dashboard_service import DashboardService
from app.core.config import settings
from app.core.logging import logger
from app.core.realtime import manager, RealtimeMessage, MessageType

# Create async engine for the worker
async_engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def _process_document_internal(record_id: int, file_path: str):
    """Internal async processing logic with real-time notification."""
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch Record
            stmt = select(MedicalRecord).where(MedicalRecord.id == record_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                logger.error(f"Task Failed: Record {record_id} not found.")
                return
            
            # 2. Run AI Pipeline (Async)
            analysis = await ai_service.process_medical_document(file_path, language_code="en")
            
            # 3. Update Record with Insights
            record.raw_text = analysis.get("raw_text", "")
            record.ai_extracted = analysis.get("structured_data", {})
            record.ai_summary = analysis.get("patient_summary", "Analyzed.")
            record.patient_summary = analysis.get("patient_summary", "Analyzed.")
            record.doctor_summary = analysis.get("doctor_summary", "")
            record.ai_processed_at = datetime.now()
            
            await db.commit()
            
            # 4. Trigger Instant Dashboard Refresh
            dashboard_service = DashboardService(db)
            dashboard_data = await dashboard_service.aggregate_dashboard_data(record.patient_id)
            
            # 5. REAL-TIME NOTIFICATION
            await manager.send_personal_message(
                RealtimeMessage(
                    type=MessageType.ANALYSIS_COMPLETE,
                    payload={
                        "record_id": record.id,
                        "patient_id": record.patient_id,
                        "type": record.type,
                        "summary": record.patient_summary,
                        "dashboard": dashboard_data
                    }
                ),
                record.patient_id # Assuming user_id maps to patient_id in this simple iteration
            )
            
            logger.info(f"Successfully processed medical record: {record_id}")
            
        except Exception as e:
            logger.error(f"Error processing record {record_id}: {e}")
            await db.rollback()

@celery_app.task(name="process_medical_document")
def process_medical_document_task(record_id: int, file_path: str):
    """Bridge Celery (sync) to Async Logic."""
    return asyncio.run(_process_document_internal(record_id, file_path))
