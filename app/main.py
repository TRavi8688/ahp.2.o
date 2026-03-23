import os
import traceback
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging, logger

setup_logging()
logger.info("STARTUP: AHP 2.0 API is initializing...")

from app.api import auth, patient, profile, doctor, doctor_verification
from app.core.realtime import manager, RealtimeMessage, MessageType
from app.core.database import get_db, engine
from app.core.limiter import limiter
from app.models.models import Base

# --- Paths to pre-built frontend static files ---
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DOCTOR_DIR = STATIC_DIR / "doctor"
PATIENT_DIR = STATIC_DIR / "patient"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup. Non-blocking — app starts even if DB is slow."""
    import asyncio
    try:
        logger.info("STARTUP: Creating database tables... (Connecting to Railway/InsForge)")
        await asyncio.wait_for(_create_tables(), timeout=60.0)
        logger.info("STARTUP: Database tables ready.")
    except asyncio.TimeoutError:
        logger.error("STARTUP: Database table creation timed out (60s). App will start anyway, but DB may be unresponsive.")
    except Exception as e:
        logger.error(f"STARTUP: Database table creation failed: {e}. App will start anyway.")

async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Log frontend static file status
    if DOCTOR_DIR.exists():
        logger.info(f"STARTUP: Doctor App static files found at {DOCTOR_DIR}")
    else:
        logger.warning(f"STARTUP: Doctor App static files NOT found at {DOCTOR_DIR}")
    if PATIENT_DIR.exists():
        logger.info(f"STARTUP: Patient App static files found at {PATIENT_DIR}")
    else:
        logger.warning(f"STARTUP: Patient App static files NOT found at {PATIENT_DIR}")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"UNHANDLED: {request.method} {request.url.path} -> {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc), "path": request.url.path}
    )

# CORS — Production-safe configuration
origins = settings.ALLOWED_ORIGINS
allow_all = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    """Lightweight request/response logging middleware."""
    try:
        response = await call_next(request)
        if response.status_code >= 400 and not request.url.path.startswith("/static"):
            logger.warning(f"HTTP {response.status_code}: {request.method} {request.url.path}")
        return response
    except Exception as e:
        logger.error(f"MIDDLEWARE_CRASH: {request.method} {request.url.path} -> {str(e)}")
        traceback.print_exc()
        raise

# ===================================================================
# API ROUTES — These MUST come before the static file mounts
# ===================================================================
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patient.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)
app.include_router(doctor_verification.router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Unconditional health check — always returns 200 so deployments never crash-loop."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Deep readiness check that verifies DB connectivity."""
    try:
        await db.execute(select(1))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Database unavailable")

# WebSocket Endpoint
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    from app.core.security import decode_token
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(payload["sub"], websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(payload["sub"], websocket)

# ===================================================================
# STATIC FILE SERVING — Doctor App & Patient App
# Mount AFTER all API routes so /api/v1/* routes take priority
# ===================================================================

# --- Doctor App (served at /doctor/) ---
if DOCTOR_DIR.exists():
    # Serve doctor static assets (JS, CSS, images)
    app.mount("/doctor/static", StaticFiles(directory=str(DOCTOR_DIR / "static")), name="doctor-static")

    @app.get("/doctor/{full_path:path}")
    async def serve_doctor_app(full_path: str):
        """Serve Doctor App — SPA catch-all returns index.html for client-side routing."""
        file_path = DOCTOR_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DOCTOR_DIR / "index.html"))

# --- Patient App (served at root /) ---
if PATIENT_DIR.exists():
    # Serve patient static assets
    patient_static = PATIENT_DIR / "static"
    if patient_static.exists():
        app.mount("/_expo/static", StaticFiles(directory=str(patient_static)), name="patient-static")

    patient_assets = PATIENT_DIR / "assets"
    if patient_assets.exists():
        app.mount("/assets", StaticFiles(directory=str(patient_assets)), name="patient-assets")

    @app.get("/{full_path:path}")
    async def serve_patient_app(full_path: str):
        """Serve Patient App — SPA catch-all returns index.html for client-side routing."""
        # Don't catch API or doctor routes
        if full_path.startswith("api/") or full_path.startswith("doctor/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = PATIENT_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(PATIENT_DIR / "index.html"))
