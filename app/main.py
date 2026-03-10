from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import auth, patient, profile, doctor
from app.core.realtime import manager, RealtimeMessage, MessageType
from app.core.database import get_db

from app.core.limiter import limiter

# Initialize Logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patient.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(doctor.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to AHP 2.0 Enterprise API", "status": "active"}

@app.get("/health")
async def health_check():
    """Liveness probe for infrastructure monitoring."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Readiness probe checking database connectivity."""
    try:
        await db.execute(select(1))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database connection failed")

# WebSocket Endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # We can handle incoming messages here if needed (e.g. chat)
            data = await websocket.receive_text()
            # Echo or process...
            await manager.send_personal_message(
                RealtimeMessage(type=MessageType.CHAT_MESSAGE, payload={"msg": "Received", "echo": data}),
                user_id
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(user_id, websocket)
