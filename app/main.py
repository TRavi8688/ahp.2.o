import os
import traceback
import time
import psutil
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging, logger

# Initialize Logging First
setup_logging()
logger.info("STARTUP: AHP 2.0 API Enterprise Initialization...")

# --- OpenTelemetry Integration ---
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

# Simple Console Exporter for Metrics (replace with PrometheusExporter in full production)
# metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
# provider = MeterProvider(metric_readers=[metric_reader])
# metrics.set_meter_provider(provider)
meter = metrics.get_meter("ahp.api")

http_request_counter = meter.create_counter(
    "http_requests_total",
    description="Total number of HTTP requests processed",
)

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
    """Liveness probe for Nginx/K8s."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- Metrics Endpoint ---
@app.get("/metrics")
async def get_metrics():
    """
    Returns system metrics (CPU, memory, disk, network) and queue diagnostics.
    """
    # FIX: interval=None prevents the 1s blocking call
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()

    metrics_data = {
        "cpu_percent": cpu_percent,
        "memory_total_gb": round(memory_info.total / (1024**3), 2),
        "memory_available_gb": round(memory_info.available / (1024**3), 2),
        "memory_used_percent": memory_info.percent,
        "disk_total_gb": round(disk_usage.total / (1024**3), 2),
        "disk_used_gb": round(disk_usage.used / (1024**3), 2),
        "disk_free_gb": round(disk_usage.free / (1024**3), 2),
        "disk_used_percent": disk_usage.percent,
        "network_bytes_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
        "network_bytes_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
        "realtime_queue_active_connections": len(manager.active_connections)
    }
    return JSONResponse(content=metrics_data)

@app.on_event("startup")
async def validate_env():
    """Validate critical environment variables at startup."""
    # FATAL: App cannot function without these
    fatal_vars = ["DATABASE_URL", "ENCRYPTION_KEY"]
    # WARNING: App stays up, but specific features (AI) will fail
    degraded_vars = ["GROQ_API_KEY", "GEMINI_API_KEY", "REDIS_URL"]
    
    missing_fatal = [v for v in fatal_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing_fatal:
        logger.critical(f"FATAL: Missing critical environment variables: {', '.join(missing_fatal)}")
        import sys
        sys.exit(1)
        
    missing_degraded = [v for v in degraded_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing_degraded:
        logger.warning(f"DEGRADED MODE: Missing optional variables {', '.join(missing_degraded)}. AI and Cache features may be disabled.")
    else:
        logger.info("ENV_VALIDATION: All system variables present.")

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
    # FATAL: App cannot function without these
    fatal_vars = ["DATABASE_URL", "ENCRYPTION_KEY"]
    # WARNING: App stays up, but specific features (AI) will fail
    degraded_vars = ["GROQ_API_KEY", "GEMINI_API_KEY", "REDIS_URL"]
    
    missing_fatal = [v for v in fatal_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing_fatal:
        logger.critical(f"FATAL: Missing critical environment variables: {', '.join(missing_fatal)}")
        import sys
        sys.exit(1)
        
    missing_degraded = [v for v in degraded_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing_degraded:
        logger.warning(f"DEGRADED MODE: Missing optional variables {', '.join(missing_degraded)}. AI and Cache features may be disabled.")
    else:
        logger.info("ENV_VALIDATION: All system variables present.")

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
# Mount built React/Expo apps
# Dockerfile copies these to /app/static/doctor and /app/static/patient
if os.path.exists("/app/static/doctor"):
    app.mount("/doctor", StaticFiles(directory="/app/static/doctor", html=True), name="doctor")
if os.path.exists("/app/static/patient"):
    app.mount("/patient", StaticFiles(directory="/app/static/patient", html=True), name="patient")

# --- Fallback / Redirect to Patient App ---
@app.get("/")
async def root_redirect():
    """Redirect root to Patient App."""
    from fastapi.responses import RedirectResponse
    # Use relative redirect to avoid domain issues
    return RedirectResponse(url="/patient/")

@app.get("/doctor/")
async def doctor_root():
    """Ensure doctor root serves index.html."""
    return FileResponse("/app/static/doctor/index.html")

@app.get("/patient/")
async def patient_root():
    """Ensure patient root serves index.html."""
    return FileResponse("/app/static/patient/index.html")
