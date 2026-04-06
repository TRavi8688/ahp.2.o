import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models import models
from app.schemas import schemas
from app.core.config import settings
from app.core.limiter import limiter
from app.core.audit import log_audit_action
from app.core.logging import logger
from app.services.dashboard_service import DashboardService
from app.services.ai_service import get_ai_service, AsyncAIService

from app.services.s3_service import upload_to_s3_async

router = APIRouter(prefix="/patient", tags=["Patient"])

# --- COMPATIBILITY ENDPOINTS for Patient App ---

@router.post("/login-ahp")
async def patient_login_ahp(
    req: schemas.LoginAHPRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """Compatibility login using Local DB with InsForge Fallback."""
    from app.core import security
    from app.core.insforge_client import insforge
    from app.api.auth import throw_auth_exception
    from app.core.audit import log_audit_action
    from app.models.models import User, Patient

    user = None
    patient = None
    ahp_id = req.ahp_id.upper().strip()

    # 1. Try Local SQLite
    result_p = await db.execute(select(Patient).where(Patient.ahp_id == ahp_id))
    patient = result_p.scalars().first()
    if patient:
        result_u = await db.execute(select(User).where(User.id == patient.user_id))
        user = result_u.scalars().first()
    
    # 2. Try InsForge Fallback (Cloud)
    if not user:
        try:
            cloud_patient = await insforge.get_one("patients", ahp_id=ahp_id)
            if cloud_patient:
                # Direct check against cloud password_hash if available
                p_hash = cloud_patient.get("password_hash")
                if p_hash and security.verify_password(req.password, p_hash):
                     # AUTO-SHADOW: Ensure this cloud user exists in the local SQLite
                     # We use the local 'id' (integer) for the JWT 'sub' to keep app logic happy
                     cloud_uuid = str(cloud_patient.get("id"))
                     
                     # 1. Try to find local user by cloud_id or email
                     stmt = select(User).where((User.insforge_id == cloud_uuid) | (User.email == cloud_patient.get("email")))
                     result_u = await db.execute(stmt)
                     local_user = result_u.scalars().first()
                     
                     if not local_user:
                         # Create local shadow user
                         local_user = User(
                             insforge_id=cloud_uuid,
                             email=cloud_patient.get("email", f"{ahp_id}@cloud.local"),
                             hashed_password=p_hash,
                             role="patient",
                             first_name=cloud_patient.get("first_name", "Cloud"),
                             last_name=cloud_patient.get("last_name", "Patient")
                         )
                         db.add(local_user)
                         await db.flush() # Get the local_user.id (Integer)
                         
                         # Create local shadow patient
                         local_patient = Patient(
                             user_id=local_user.id,
                             ahp_id=ahp_id,
                             phone_number=cloud_patient.get("phone_number", ""),
                             age=cloud_patient.get("age"),
                             blood_group=cloud_patient.get("blood_group"),
                             gender=cloud_patient.get("gender")
                         )
                         db.add(local_patient)
                         await db.commit()
                     else:
                         # Update existing local user with cloud metadata if needed
                         if not local_user.insforge_id:
                             local_user.insforge_id = cloud_uuid
                             await db.commit()

                     # 2. IMPORTANT: The JWT 'sub' is the LOCAL INTEGER ID
                     access_token = security.create_access_token(local_user.id, "patient")
                     refresh_token = security.create_refresh_token(local_user.id, "patient")
                     return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "bearer",
                        "ahp_id": ahp_id
                     }
        except Exception as e:
            logger.error(f"InsForge Fallback failed: {e}")

    # Final Verification
    if not user or not security.verify_password(req.password, user.hashed_password):
        await log_audit_action(db, "LOGIN_FAILURE_AHP", resource_type="USER", details={"ahp_id": ahp_id})
        throw_auth_exception("Invalid Mulajna ID or password")
    
    access_token = security.create_access_token(user.id, user.role)
    refresh_token = security.create_refresh_token(user.id, user.role)
    
    await log_audit_action(db, "LOGIN_SUCCESS_AHP", user_id=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "ahp_id": ahp_id
    }

# --- STANDARD PATIENT ENDPOINTS ---

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload-report", response_model=schemas.ReportAnalysisResponse)
@limiter.limit("5/minute")
async def upload_report(
    request: Request,
    file: UploadFile = File(...),
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db),
    ai: AsyncAIService = Depends(get_ai_service)
):
    """Securely uploads and asynchronously processes a medical report (C1K Big Pipeline Optimized)."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    import shutil
    import asyncio
    from arq import create_pool
    from arq.connections import RedisSettings
    from app.services.s3_service import upload_to_s3_async

    # --- BIG PIPELINE: Global Backpressure (C1K Throttle) ---
    if not settings.DEMO_MODE:
        try:
            redis_bp = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
            current_depth = await redis_bp.llen("arq:queue")
            if current_depth > 500: # Increased from 50 for Big Pipeline capacity
                logger.error(f"PIPELINE_CONGESTION: Queue depth {current_depth} > threshold 500.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Chitti is analyzing a heavy backlog. Parallel pipelines are full. Please try in 2 mins.",
                    headers={"Retry-After": "120"}
                )
        except HTTPException:
            raise
        except Exception as bp_err:
            logger.warning(f"BACKPRESSURE_BYPASS: Redis check failed ({bp_err}).")

    try:
        # 1. Non-blocking parallel file IO
        await asyncio.to_thread(os.makedirs, "temp_uploads", exist_ok=True)
        safe_filename = f"{uuid.uuid4()}{ext}"
        temp_path = os.path.join("temp_uploads", safe_filename)
        
        # Async-friendly streaming from SpooledTemporaryFile to disk
        def _save_file():
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        await asyncio.to_thread(_save_file)

        # 2. Async Upload to Cloud Storage (Zero-Blocking)
        s3_object_name = f"reports/{current_patient.ahp_id or 'anon'}/{safe_filename}"
        s3_url = await upload_to_s3_async(temp_path, s3_object_name)

        # 3. Create Placeholder Record
        new_record = models.MedicalRecord(
            patient_id=current_patient.id,
            type="Document",
            file_url=s3_url,
            raw_text="[PIPELINE_ANALYSIS_STAGED]",
            ai_summary="Chitti is decoding your clinical data...",
            patient_summary="Analysis staged in cloud pipeline."
        )
        db.add(new_record)
        await db.commit()

        # 4. ENQUEUE TO ARQ WORKER (Parallel Flow)
        job_id = "demo_job_analysis"
        if not settings.DEMO_MODE:
            try:
                redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
                job = await redis.enqueue_job('process_medical_document_task', new_record.id, s3_object_name)
                job_id = job.job_id
            except Exception as queue_err:
                logger.error(f"QUEUE_ERROR: {queue_err}")
                job_id = "no_queue"

        # Non-blocking cleanup
        await asyncio.to_thread(os.remove, temp_path)

        await log_audit_action(
            db, 
            "REPORT_STAGED_IN_PIPELINE", 
            user_id=current_patient.user_id, 
            resource_type="MEDICAL_RECORD",
            details={"record_id": new_record.id, "job_id": job_id, "node": os.getenv("HOSTNAME", "node-1")}
        )
        
        return {
            "status": "processing",
            "record_id": new_record.id,
            "job_id": job_id,
            "message": "Clinical data successfully staged in parallel pipeline.",
            "url": s3_url
        }

    except Exception as e:
        logger.error(f"PIPELINE_FAILURE: {str(e)}")
        raise HTTPException(status_code=500, detail="Clinical pipeline failure. Incident logged.")

@router.post("/confirm-and-save-report")
async def confirm_report(
    data: schemas.ReportConfirmSave,
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Saves the AI analyzed report to the permanent database history."""
    new_record = models.MedicalRecord(
        patient_id=current_patient.id,
        type=data.type,
        file_url=data.s3_url,
        raw_text=data.analysis.get("raw_text"),
        ai_extracted=data.analysis.get("structured_data"),
        ai_summary=data.analysis.get("summary")
    )
    db.add(new_record)
    
    if data.update_profile:
        # Add conditions and meds to profile
        for c in data.analysis.get("structured_data", {}).get("conditions", []):
            db.add(models.Condition(patient_id=current_patient.id, name=c["name"], added_by="ai"))
        for m in data.analysis.get("structured_data", {}).get("medications", []):
            db.add(models.Medication(patient_id=current_patient.id, generic_name=m["name"], added_by="ai"))
            
    await db.commit()
    return {"status": "success", "record_id": new_record.id}

@router.get("/records", response_model=List[schemas.MedicalRecordResponse])
async def get_my_records(
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    result = await db.execute(
        select(models.MedicalRecord).where(models.MedicalRecord.patient_id == current_patient.id)
    )
    return result.scalars().all()

@router.get("/profile", response_model=schemas.PatientProfileResponse)
async def get_patient_profile(
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Retrieves the full profile of the authenticated patient."""
    # Ensure user is loaded
    result = await db.execute(select(models.User).where(models.User.id == current_patient.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {
            "id": current_patient.id,
            "full_name": "Valued Patient",
            "email": "patient@ahp.local",
            "phone_number": current_patient.phone_number or "N/A",
            "ahp_id": current_patient.ahp_id,
            "age": current_patient.age,
            "blood_group": current_patient.blood_group,
            "gender": current_patient.gender,
            "recent_records": []
        }
    
    return {
        "id": current_patient.id,
        "full_name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "phone_number": current_patient.phone_number,
        "ahp_id": current_patient.ahp_id,
        "age": current_patient.age,
        "blood_group": current_patient.blood_group,
        "gender": current_patient.gender,
        "recent_records": [] # Can be populated via join if needed
    }

@router.get("/clinical-summary")
async def get_clinical_summary(
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Returns AI-generated clinical insights for the dashboard."""
    # Mock/Aggregated data for the test drive
    return {
        "summary": "Your health metrics are stable. Blood pressure is in range. Recent labs show optimal glucose levels. Continue your current medication as prescribed.",
        "health_score": 88,
        "health_score_factors": ["Normal BP", "Consistent Meds", "Clean X-Ray"],
        "last_update": "Today",
        "recovery_timeline": [
            {"year": "2023", "level": 40},
            {"year": "2024", "level": 60},
            {"year": "2025", "level": 85},
            {"year": "2026", "level": 88}
        ],
        "condition_progress": {
            "Hypertension": [{"value": "130/90", "date": "Jan"}, {"value": "120/80", "date": "Mar"}],
            "Diabetes": [{"value": "110", "date": "Jan"}, {"value": "95", "date": "Mar"}]
        },
        "medication_impact": [
            {"name": "Metformin", "improvement": "+15%"},
            {"name": "Amlodipine", "improvement": "+10%"}
        ],
        "alerts": ["Annual checkup due in 5 days."]
    }

@router.post("/set-password")
async def set_patient_password(
    data: schemas.SetPasswordRequest,
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Updates the patient's login password and generates an AHP ID if missing."""
    from app.core import security
    
    # Update linked User password
    result = await db.execute(select(models.User).where(models.User.id == current_patient.user_id))
    user = result.scalar_one()
    user.hashed_password = security.pwd_context.hash(data.password)
    
    # Ensure AHP ID exists (for new registrations)
    if not current_patient.ahp_id:
        current_patient.ahp_id = f"AHP-{uuid.uuid4().hex[:8].upper()}"
    
    await db.commit()
    return {"status": "success", "ahp_id": current_patient.ahp_id}

@router.get("/dashboard")
async def get_dashboard(
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    service = DashboardService(db)
    return await service.get_dashboard(current_patient.id)

@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_chitti(
    request: Request,
    text: Optional[str] = Form(None),
    language_code: str = Form("en-IN"),
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(deps.get_db_user),
    db: AsyncSession = Depends(deps.get_db),
    ai: AsyncAIService = Depends(get_ai_service)
):
    """Interactive AI chat with memory, vision, and voice capability."""
    conversation_id = f"chat_{current_user.id}"
    
    msg_content = text or "Attached media"
    image_bytes = None
    audio_bytes = None
    
    if file:
        file_bytes = await file.read()
        image_bytes = file_bytes
        msg_content += " (Image attached)"

    if audio:
        audio_bytes = await audio.read()
        msg_content += " (Voice message attached)"

    # Generate AI response using memory, vision, and language preference
    ai_text = await ai.chat_with_memory(
        str(current_user.id), 
        conversation_id, 
        msg_content, 
        image_bytes=image_bytes, 
        audio_bytes=audio_bytes,
        language_code=language_code,
        db=db
    )
    
    return {
        "ai_text": ai_text,
        "conversation_id": conversation_id
    }

@router.get("/chat-history", response_model=List[schemas.ChatMessageResponse])
async def get_chat_history(
    current_user: models.User = Depends(deps.get_db_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """Retrieve verified chat history from the local database."""
    result = await db.execute(
        select(models.Message).where(models.Message.user_id == current_user.id).order_by(models.Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        schemas.ChatMessageResponse(
            sender="user" if m.role == "user" else "ai",
            message_text=m.content,
            created_at=m.created_at
        ) for m in messages
    ]

@router.get("/pending-access")
async def get_pending_access(
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Fetch any pending doctor access requests for the patient."""
    stmt = select(models.DoctorAccess).where(
        models.DoctorAccess.patient_id == current_patient.id,
        models.DoctorAccess.status == "requested"
    )
    result = await db.execute(stmt)
    requests = result.scalars().all()
    
    return [
        {
            "access_id": r.id,
            "doctor_name": r.doctor_name,
            "clinic_name": r.clinic_name,
            "access_level": r.access_level,
            "requested_at": r.created_at
        } for r in requests
    ]

@router.post("/approve-access/{access_id}")
async def approve_access(
    access_id: int,
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Approve a doctor's request to view medical records."""
    stmt = select(models.DoctorAccess).where(
        models.DoctorAccess.id == access_id,
        models.DoctorAccess.patient_id == current_patient.id
    )
    result = await db.execute(stmt)
    access_req = result.scalar_one_or_none()
    
    if not access_req:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    access_req.status = "granted"
    from datetime import datetime
    access_req.granted_at = datetime.now()
    
    await db.commit()
    await log_audit_action(db, "ACCESS_GRANTED", user_id=current_patient.user_id, details={"doctor": access_req.doctor_name})
    
    return {"status": "success", "message": f"Access granted to {access_req.doctor_name}"}

@router.post("/revoke-access/{access_id}")
async def revoke_access(
    access_id: int,
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Revoke or reject a doctor's access."""
    stmt = select(models.DoctorAccess).where(
        models.DoctorAccess.id == access_id,
        models.DoctorAccess.patient_id == current_patient.id
    )
    result = await db.execute(stmt)
    access_req = result.scalar_one_or_none()
    
    if not access_req:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    access_req.status = "revoked"
    await db.commit()
    await log_audit_action(db, "ACCESS_REVOKED", user_id=current_patient.user_id, details={"doctor": access_req.doctor_name})
    
    return {"status": "success", "message": f"Access revoked for {access_req.doctor_name}"}

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_patient: models.Patient = Depends(deps.get_current_patient),
    db: AsyncSession = Depends(deps.get_db)
):
    """Polls the status of a background AI processing job."""
    from arq.connections import RedisSettings
    from arq.jobs import Job, JobStatus
    from arq import create_pool
    
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job_handle = Job(job_id, redis)
    status = await job_handle.status()
    
    # Map Arq status to our simpler schema
    status_map = {
        JobStatus.queued: "queued",
        JobStatus.deferred: "queued",
        JobStatus.in_progress: "in_progress",
        JobStatus.complete: "completed",
        JobStatus.not_found: "not_found"
    }
    
    friendly_status = status_map.get(status, "unknown")
    result = None
    if status == JobStatus.complete:
        result_info = await job_handle.result_info()
        result = {"success": True, "info": str(result_info)}
    
    return {
        "job_id": job_id,
        "status": friendly_status,
        "result": result
    }
