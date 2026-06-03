from typing import Annotated
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from uuid import UUID
from jose import jwt, JWTError
import json

from services.websocket_manager import manager
from services.security import SECRET_KEY, ALGORITHM
from db.database import async_session_maker
from repositories.user import UserRepository

router = APIRouter()

async def get_user_from_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return UUID(str(user_id))
    except (JWTError, ValueError):
        return None
    return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Annotated[str, Query()]
):
    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=4003) # Forbidden
        return

    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Protocol handling
            msg_type = message_data.get("type")
            
            if msg_type == "join_room":
                room_id = message_data.get("room_id")
                if room_id:
                    await manager.join_room(UUID(room_id), user_id)
            
            elif msg_type == "leave_room":
                room_id = message_data.get("room_id")
                if room_id:
                    await manager.leave_room(UUID(room_id), user_id)
            
            # Heartbeat/Ping to keep connection alive
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception:
        manager.disconnect(user_id)
        await websocket.close()
