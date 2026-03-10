import json
from enum import Enum
from typing import Dict, Set, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.core.logging import logger

class MessageType(str, Enum):
    NEW_RECORD = "new_record"
    ANALYSIS_COMPLETE = "analysis_complete"
    DASHBOARD_UPDATE = "dashboard_update"
    CHAT_MESSAGE = "chat_message"
    CONSULTATION_START = "consultation_start"

class RealtimeMessage(BaseModel):
    type: MessageType
    payload: Dict[str, Any]
    sender_id: Optional[str] = None
    target_id: Optional[str] = None

class ConnectionManager:
    def __init__(self):
        # active_connections[user_id] = {websocket1, websocket2, ...}
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Active connections: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected.")

    async def send_personal_message(self, message: RealtimeMessage, user_id: int):
        if user_id in self.active_connections:
            data = message.model_dump_json()
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(data)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(user_id, conn)

    async def broadcast(self, message: RealtimeMessage):
        data = message.model_dump_json()
        for user_id, connections in self.active_connections.items():
            disconnected = []
            for connection in connections:
                try:
                    await connection.send_text(data)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(user_id, conn)

manager = ConnectionManager()
