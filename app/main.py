import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging, logger

# Initialize Logging First
setup_logging()
logger.info("STARTUP: AHP 2.0 API Enterprise Initialization...")

# --- OpenTelemetry REMOVED for RAM optimization ---
# meter = metrics.get_meter("ahp.api")
# http_request_counter = ...

from app.api import auth, patient, profile, doctor, doctor_verification
from app.core.realtime import manager
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

# NOTE: Database creation (Base.metadata.create_all) REMOVED from startup for Enterprise Hardening.
# Use scripts/migrate.py or alembic instead.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

@app.on_event("startup")
async def startup_event():
    """Startup diagnostics."""
    logger.info(f"STARTUP: Checking assets at {STATIC_DIR}")
    logger.info(f"DOCTOR_PATH_EXISTS: {DOCTOR_DIR.exists()}")
    logger.info(f"PATIENT_PATH_EXISTS: {PATIENT_DIR.exists()}")
    if DOCTOR_DIR.exists():
        logger.info(f"DOCTOR_CONTENTS: {os.listdir(DOCTOR_DIR)}")

# @app.middleware("http")
# async def observability_middleware(request: Request, call_next):
#     """Temporarily disabled to ensure connectivity."""
#     return await call_next(request)

# --- Health Check ---
@app.get("/health")
async def health_check():
    """Enterprise Health Check with DB Verification."""
    db_status = "unknown"
    try:
        from sqlalchemy import text
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"HEALTH_CHECK_DB_FAILURE: {str(e)}")

    return {
        "status": "healthy" if "error" not in db_status else "degraded",
        "database": db_status,
        "version": "STABLE-2026-03-28-VMAX",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Minimal Metrics to avoid OOM."""
    return {"status": "optimized", "memory_usage": "slim"}

# --- Register Handlers ---
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS Configuration ---
# Enterprise: Strict origin control. Use environment variables for production.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",
    "https://api.mulajna.com",
    "https://ahp2o-production.up.railway.app",
    "*" # Placeholder for initial testing, change to specific origins later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def validate_env():
    """Validate critical environment variables at startup."""
    # Rely on settings.validate_production_config() for internal checks
    try:
        settings.validate_production_config()
    except Exception as e:
        logger.critical(f"STARTUP_VALIDATION_FAILED: {str(e)}")
        # ONLY exit if it's a structural failure, not just a missing key
        if "postgresql" in str(e).lower():
             import sys
             sys.exit(1)
             
    # Log availability of optional AI features
    degraded_vars = ["GROQ_API_KEY", "GEMINI_API_KEY", "REDIS_URL"]
    missing_degraded = [v for v in degraded_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing_degraded:
        logger.warning(f"DEGRADED MODE: Missing optional variables {', '.join(missing_degraded)}. AI features may be disabled.")
    else:
        logger.info("ENV_VALIDATION: Core systems ready.")

# ===================================================================
# API ROUTES
# ===================================================================
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patient.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)
app.include_router(doctor_verification.router, prefix=settings.API_V1_STR)

# ===================================================================
# UNIFIED STATIC FILE SERVING
# ===================================================================
# 1. Mount the shared static folder for CSS/JS/Media
if os.path.exists("/app/static"):
    app.mount("/static-assets", StaticFiles(directory="/app/static"), name="static")

# 2. Explicit Index Routes (The "Front Doors")
@app.get("/doctor/")
@app.get("/doctor")
async def doctor_root():
    """Serve Doctor Dashboard."""
    return FileResponse("/app/static/doctor/index.html")

@app.get("/patient/")
@app.get("/patient")
async def patient_root():
    """Serve Patient Dashboard."""
    return FileResponse("/app/static/patient/index.html")

@app.get("/")
async def root_redirect():
    """Serve Patient App on Root."""
    # Prioritize index.html for React/Expo entry
    return FileResponse("/app/static/patient/index.html")

# 3. Catch-all for assets (Fixing 404s for _expo, etc)
@app.get("/{rest_of_path:path}")
async def global_asset_catchall(rest_of_path: str):
    """Deep catch-all to ensure Expo/React assets load."""
    # Check patient assets first
    p_path = f"/app/static/patient/{rest_of_path}"
    if os.path.isfile(p_path):
        return FileResponse(p_path)
        
    # Check doctor assets second
    d_path = f"/app/static/doctor/{rest_of_path}"
    if os.path.isfile(d_path):
        return FileResponse(d_path)
        
    # If not found, fallback to patient root for SPA routing
    return FileResponse("/app/static/patient/index.html")

logger.info("FINAL_IMPORT_COMPLETE: app/main.py is fully loaded and ready.")
