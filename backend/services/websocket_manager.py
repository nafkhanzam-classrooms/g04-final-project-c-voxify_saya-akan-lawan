from typing import Dict, List, Set
from fastapi import WebSocket
from uuid import UUID
import json

class ConnectionManager:
    def __init__(self):
        # active_connections: {user_id: WebSocket}
        self.active_connections: Dict[UUID, WebSocket] = {}
        # room_members: {room_id: set(user_id)}
        self.room_members: Dict[UUID, Set[UUID]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove from all rooms
        for room_id in self.room_members:
            if user_id in self.room_members[room_id]:
                self.room_members[room_id].remove(user_id)

    async def join_room(self, room_id: UUID, user_id: UUID):
        if room_id not in self.room_members:
            self.room_members[room_id] = set()
        self.room_members[room_id].add(user_id)

    async def leave_room(self, room_id: UUID, user_id: UUID):
        if room_id in self.room_members and user_id in self.room_members[room_id]:
            self.room_members[room_id].remove(user_id)

    async def send_personal_message(self, message: dict, user_id: UUID):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

    async def broadcast_to_room(self, room_id: UUID, message: dict):
        if room_id in self.room_members:
            message_json = json.dumps(message)
            for user_id in self.room_members[room_id]:
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message_json)

# Global manager instance
manager = ConnectionManager()
