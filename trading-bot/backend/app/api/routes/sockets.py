from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.api.routes.legacy import multi_status
from starlette.websockets import WebSocketState
import asyncio
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Broadcast connections (Status monitoring)
        self.active_connections: list[WebSocket] = []
        # Support & Security connections (User-specific)
        self.user_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            logger.info(f"User {user_id} connected to real-time notification socket.")
        else:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
        elif websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be stale
                    pass

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            with SessionLocal() as db:
                data = multi_status(db)
                await websocket.send_json(data)
            await asyncio.sleep(2)
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)

@router.websocket("/ws/notifications/{user_id}")
async def notification_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id=user_id)
    try:
        while True:
            # Wait for any incoming client message (keepalive)
            data = await websocket.receive_text()
            # Users could send messages here if we wanted bidirectional WS-chat
            # But we use REST for message submission and WS for push notifications
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from notification socket.")
    finally:
        manager.disconnect(websocket, user_id=user_id)
