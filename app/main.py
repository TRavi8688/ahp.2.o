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
    logger.info("STARTUP: Running system readiness check...")
    if not DOCTOR_DIR.exists(): logger.warning(f"DOCTOR_APP: Static files missing at {DOCTOR_DIR}")
    if not PATIENT_DIR.exists(): logger.warning(f"PATIENT_APP: Static files missing at {PATIENT_DIR}")

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Enhanced observability with OpenTelemetry metrics and correlation IDs."""
    import uuid
    from structlog.contextvars import bind_contextvars
    
    request_id = str(uuid.uuid4())
    bind_contextvars(request_id=request_id)
    start_time = time.time()
    
    # Increment Metrics
    http_request_counter.add(1, {"method": request.method, "path": request.url.path})
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        if response.status_code >= 400 and not request.url.path.startswith("/static"):
            logger.warning(f"HTTP {response.status_code}: {request.method} {request.url.path}", 
                          request_id=request_id, latency_ms=process_time)
        return response
    except Exception as e:
        logger.error(f"SYSTEM_CRASH: {request.method} {request.url.path} -> {str(e)}", request_id=request_id)
        raise

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
    critical_vars = ["GROQ_API_KEY", "GEMINI_API_KEY", "DATABASE_URL", "REDIS_URL", "ENCRYPTION_KEY"]
    missing = [v for v in critical_vars if not os.getenv(v) and not getattr(settings, v.lower(), None)]
    if missing:
        logger.critical(f"FATAL: Missing critical environment variables: {', '.join(missing)}")
        import sys
        sys.exit(1)
    logger.info("ENV_VALIDATION: All critical variables present.")

# ... (CORS and logic remains the same)

# ===================================================================
# API ROUTES
# ===================================================================
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patient.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)
app.include_router(doctor_verification.router, prefix=settings.API_V1_STR)

# ===================================================================
# UNIFIED API ROUTING (Static files served by Nginx)
# ===================================================================

# --- Fallback / Redirect to Nginx-served Patient App ---
@app.get("/")
async def root_redirect():
    """Redirect root to Patient App (Served by Nginx)."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/patient/")
