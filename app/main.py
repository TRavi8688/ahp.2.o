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
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.models import Base
from app.core.middleware import IdempotencyMiddleware, RequestIDMiddleware

# 1. Initialize Structured Logging early
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs" if not os.environ.get("ENVIRONMENT") == "production" else None,
    redoc_url=None
)

from app.core.metrics import instrument_request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# 2. MIDDLEWARE CHAIN (Order is Critical)
# Traceability & Metrics first
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(instrument_request())
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idempotency (Must be after RequestID for logging correlation)
app.add_middleware(IdempotencyMiddleware)

@app.on_event("startup")
async def startup_event():
    """Enterprise startup diagnostics."""
    logger.info("STARTUP: Production API Mode Active.")

# --- GOOGLE-GRADE SRE PROBES ---

@app.get("/healthz", tags=["Infrastructure"])
async def liveness_probe():
    """Liveness probe: Checks if the process is alive."""
    return {"status": "alive"}

@app.get("/readyz", tags=["Infrastructure"])
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Readiness probe: Checks if subsystems are ready."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"READINESS_FAILURE: {e}")
        return JSONResponse(status_code=503, content={"status": "not_ready"})

@app.get("/health", tags=["Infrastructure"])
async def health_check(db: AsyncSession = Depends(get_db)):
    return await readiness_probe(db)

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("SHUTDOWN: Draining resources...")

@app.get("/metrics", tags=["Infrastructure"])
async def get_metrics():
    """Prometheus metrics endpoint for external collectors."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- REGISTER HANDLERS & ROUTES ---
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patient.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)
app.include_router(doctor_verification.router, prefix=settings.API_V1_STR)

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Secure WebSocket Bridge for Real-time Notifications & Chat."""
    from app.core import security
    from fastapi import WebSocketDisconnect
    
    try:
        payload = security.decode_token(token, token_type="access")
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = int(payload.get("sub"))
        await manager.connect(user_id, websocket)
        
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WS_ERROR: {str(e)}")
        manager.disconnect(user_id, websocket)

logger.info("SYSTEM_READY: AHP 2.0 API is fully initialized.")
