import json
import socket
from typing import Dict, List, Set
from uuid import UUID


class ConnectionManager:
    def __init__(self):
        # active_connections: {user_id: socket.socket}
        self.active_connections: Dict[UUID, socket.socket] = {}
        # room_members: {room_id: set(user_id)}
        self.room_members: Dict[UUID, Set[UUID]] = {}

    def connect(self, user_id: UUID, sock: socket.socket):
        self.active_connections[user_id] = sock

    def disconnect(self, user_id: UUID):
        if user_id in self.active_connections:
            # We don't close the socket here as it might be managed by the server loop
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

    def _send_message(self, sock: socket.socket, message: dict):
        try:
            payload = json.dumps(message).encode("utf-8")
            # 4-byte big-endian length prefix
            header = len(payload).to_bytes(4, byteorder="big")
            sock.sendall(header + payload)
        except (socket.error, BrokenPipeError):
            # Handle disconnection if needed
            pass

    async def send_personal_message(self, message: dict, user_id: UUID):
        if user_id in self.active_connections:
            self._send_message(self.active_connections[user_id], message)

    async def broadcast_to_room(self, room_id: UUID, message: dict):
        if room_id in self.room_members:
            for user_id in self.room_members[room_id]:
                if user_id in self.active_connections:
                    self._send_message(self.active_connections[user_id], message)


# Global manager instance
manager = ConnectionManager()
