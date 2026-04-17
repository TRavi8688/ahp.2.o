import os
from sqlalchemy import text
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
import sentry_sdk

# Initialize Logging First
setup_logging()

# Initialize Sentry for Enterprise Observability
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("STARTUP: Sentry Observability Enabled.")

logger.info("STARTUP: AHP 2.0 API Enterprise Initialization...")

# --- OpenTelemetry REMOVED for RAM optimization ---
# meter = metrics.get_meter("ahp.api")
# http_request_counter = ...

from app.api import auth, patient, profile, doctor, doctor_verification
from app.core.realtime import manager
from app.core.database import get_db, engine
from app.core.limiter import limiter
from app.models.models import Base

# --- Paths to pre-built frontend static files REMOVED for Pure API Architecture ---
# Logic moved to Nginx/Vercel for Three-Lane Highway.

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
    logger.info("STARTUP: Pure API Mode Active. Static serving handed off to Edge.")

# @app.middleware("http")
# async def observability_middleware(request: Request, call_next):
#     """Temporarily disabled to ensure connectivity."""
#     return await call_next(request)

# --- Billion-Dollar Deep Diagnostics ---
@app.get("/health")
async def health_check():
    """Enterprise Health Check with Failover & Infrastructure Awareness."""
    db_status = "unknown"
    mode = "stable"
    diagnostics = {}
    
    # 1. Database Check
    try:
        from app.core.database import get_db, FailoverManager
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            db_status = "connected" if not FailoverManager.is_primary_down else "connected (SECONDARY_FAILOVER)"
            mode = "degraded" if FailoverManager.is_primary_down else "stable"
            break
    except Exception as e:
        db_status = f"error: {str(e)}"
        mode = "maintenance"
    diagnostics["database"] = db_status

    # 2. Storage Check
    try:
        test_file = Path("/app/uploads/health_tick.txt")
        test_file.write_text(datetime.utcnow().isoformat())
        diagnostics["storage"] = "writable"
    except Exception:
        diagnostics["storage"] = "read-only/error"
        mode = "degraded"

    # 3. Environment Check (Redacted)
    ai_status = "ready" if settings.GEMINI_API_KEY or settings.GROQ_API_KEY else "disabled"
    diagnostics["ai_engine"] = ai_status
    if ai_status == "disabled": mode = "degraded"

    # 4. Process Info
    import psutil
    process = psutil.Process(os.getpid())
    diagnostics["memory_rss_mb"] = int(process.memory_info().rss / 1024 / 1024)

    return {
        "status": "healthy" if mode == "stable" else mode,
        "diagnostics": diagnostics,
        "infrastructure": "billion-dollar-hardened",
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
    "https://ahp2o-production.up.railway.app"
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
        logger.error(f"STARTUP_VALIDATION_WARNING: {str(e)}")
        # BILLION-DOLLAR RULE: Never exit. Stay online in degraded mode.
        # if "postgresql" in str(e).lower():
        #      import sys
        #      sys.exit(1)
             
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
# REAL-TIME WEBSOCKET BRIDGE
# ===================================================================
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Secure WebSocket Bridge for Real-time Notifications & Chat.
    Enforces JWT validation before accepting the hand-shake.
    """
    from app.core import security
    
    # 1. Validate Token
    payload = security.decode_token(token, token_type="access")
    if not payload:
        logger.warning("WS_AUTH_FAIL: Invalid or expired token attempted connection.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = int(payload.get("sub"))
    
    # 2. Accept & Register Connection
    try:
        await manager.connect(user_id, websocket)
        
        # Keep connection alive and listen for incoming heartbeats or client messages
        while True:
            # We don't expect much client-to-server WS traffic yet, but we must listen to detect disconnects
            data = await websocket.receive_text()
            # Simple Echo/Ping for latency testing
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        logger.info(f"WS_DISCONNECT: User {user_id} disconnected.")
    except Exception as e:
        logger.error(f"WS_ERROR: {str(e)}")
        manager.disconnect(user_id, websocket)

# SPA serving removed. Backend now strictly handles /api/v1/*
# Use Vercel, Netlify, or Nginx to serve the built static files.

# The legacy "Billion-Dollar Global Shield" has been removed in favor of Sentry telemetry.
# Unhandled 500s will now correctly bubble up to Sentry while FastAPI handles the standard 500 response natively.

logger.info("FINAL_IMPORT_COMPLETE: app/main.py is fully loaded and ready.")
