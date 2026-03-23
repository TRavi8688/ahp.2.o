import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from arq.connections import RedisSettings

from app.models.models import MedicalRecord
from app.services.ai_service import AsyncAIService
from app.services.dashboard_service import DashboardService
from app.core.config import settings
from app.core.logging import logger
from app.core.realtime import manager, RealtimeMessage, MessageType

# Create async engine for the worker exactly as before, but ARQ allows native execution
async_engine = create_async_engine(settings.async_database_url)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def startup(ctx):
    """ARQ context startup. Here we cleanly inject dependencies instead of relying on global singletons."""
    ctx['ai_service'] = AsyncAIService()
    logger.info("ARQ Worker started and AI Service injected.")

async def shutdown(ctx):
    """Cleanup hook for native async workers."""
    logger.info("ARQ Worker shutting down cleanly.")

async def process_medical_document_task(ctx, record_id: int, object_key: str):
    """Native async processing logic. Using S3 object keys instead of local paths."""
    ai_service: AsyncAIService = ctx['ai_service']
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch Record
            stmt = select(MedicalRecord).where(MedicalRecord.id == record_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                logger.error(f"Task Failed: Record {record_id} not found.")
                return
            
            # 2. Run AI Pipeline (Uses S3 Key, handles its own retrieval)
            analysis = await ai_service.process_medical_document(object_key, language_code="en")
            
            if "error" in analysis:
                logger.error(f"AI Pipeline failed for {object_key}: {analysis['error']}")
                raise Exception(f"AI Processing Failed: {analysis['error']}") # Trigger ARQ retry
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
            
            # 5. REAL-TIME NOTIFICATION (Uses Redis PubSub natively now)
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
                record.patient_id
            )
            
            logger.info(f"Successfully processed medical record: {record_id} via ARQ Worker")
            
        except Exception as e:
            logger.error(f"ARQ Error processing record {record_id}: {e}")
            await db.rollback()

class WorkerSettings:
    """ARQ explicit settings definition."""
    functions = [process_medical_document_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries = 5 # Allow retries for transient AI errors
    retry_delay = 10 # Base delay between retries

