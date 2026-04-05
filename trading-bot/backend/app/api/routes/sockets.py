from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.api.routes.legacy import multi_status
from starlette.websockets import WebSocketState
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection)
            else:
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Check if socket is still connected before processing
            if websocket.client_state != WebSocketState.CONNECTED:
                break
                
            with SessionLocal() as db:
                try:
                    data = multi_status(db)
                    await websocket.send_json(data)
                except (WebSocketDisconnect, asyncio.CancelledError):
                    break
                except RuntimeError as e:
                    if "close message has been sent" in str(e).lower() or "disconnected" in str(e).lower():
                        break
                    logger.error(f"WS Runtime Error: {e}")
                    break
                except Exception as e:
                    # Generic catch-all for other sync errors
                    if "disconnect" in str(e).lower() or "closed" in str(e).lower():
                        break
                    logger.error(f"WS Sync Error: {e}", exc_info=True)
                    break
            
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                # Normal termination during server shutdown
                return
    except WebSocketDisconnect:
        logger.info("Client disconnected normally.")
    except Exception as e:
        logger.error(f"WebSocket Loop Error: {e}")
    finally:
        manager.disconnect(websocket)
