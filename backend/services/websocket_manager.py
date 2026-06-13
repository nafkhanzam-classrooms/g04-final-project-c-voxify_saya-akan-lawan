import socket
import threading
from typing import Dict, Set, Optional
from uuid import UUID
from utils.protocol import send_message


class ConnectionManager:
    def __init__(self):
        # active_connections: {user_id: set(socket)}
        self.active_connections: Dict[UUID, Set[socket.socket]] = {}
        # room_members: {room_id: set(user_id)}
        self.room_members: Dict[UUID, Set[UUID]] = {}
        # Lock untuk thread safety — hanya lindungi akses ke dict, bukan I/O
        self.lock = threading.Lock()

    def connect(self, user_id: UUID, sock: socket.socket):
        with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(sock)
            print(f"[MANAGER] User {user_id} connected. Sockets: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: UUID, sock: socket.socket) -> bool:
        with self.lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(sock)
                remaining = len(self.active_connections[user_id])
                print(f"[MANAGER] User {user_id} disconnected. Remaining sockets: {remaining}")
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    # Hapus dari semua room
                    for room_id in self.room_members:
                        self.room_members[room_id].discard(user_id)
                    print(f"[MANAGER] User {user_id} has NO MORE sockets. Returning True.")
                    return True
            else:
                print(f"[MANAGER] User {user_id} NOT FOUND in active_connections during disconnect.")
            return False

    def join_room(self, room_id: UUID, user_id: UUID):
        with self.lock:
            if room_id not in self.room_members:
                self.room_members[room_id] = set()
            self.room_members[room_id].add(user_id)

    def leave_room(self, room_id: UUID, user_id: UUID):
        with self.lock:
            if room_id in self.room_members:
                self.room_members[room_id].discard(user_id)

    def send_personal_message(self, message: dict, user_id: UUID):
        # Ambil socket di dalam lock, kirim di LUAR lock.
        with self.lock:
            sockets = list(self.active_connections.get(user_id, set()))

        for sock in sockets:
            try:
                send_message(sock, message)
                print(f"[*] Sent personal message to user {user_id}")
            except socket.error:
                print(f"[!] Failed to send personal message to user {user_id}")

    def broadcast_to_room(self, room_id: UUID, message: dict):
        # Snapshot semua socket target di dalam lock, kirim di LUAR lock.
        # Jika satu klien lambat, klien lain dan operasi manager tidak terhambat.
        with self.lock:
            member_ids = list(self.room_members.get(room_id, set()))
            targets = []
            for uid in member_ids:
                if uid in self.active_connections:
                    for s in self.active_connections[uid]:
                        targets.append((uid, s))

        print(f"[*] Broadcasting to room {room_id}: {len(targets)} recipient(s)")
        for user_id, sock in targets:
            try:
                send_message(sock, message)
            except socket.error:
                print(f"[!] Failed to send broadcast to user {user_id} in room {room_id}")

    def broadcast_global(self, message: dict):
        """Kirim pesan broadcast ke seluruh user yang sedang terkoneksi."""
        with self.lock:
            targets = []
            for uid, socks in self.active_connections.items():
                for s in socks:
                    targets.append((uid, s))
        
        print(f"[*] Broadcasting globally to {len(targets)} client(s)")
        for user_id, sock in targets:
            try:
                send_message(sock, message)
            except socket.error:
                print(f"[!] Failed to send global broadcast to user {user_id}")


# Global manager instance
manager = ConnectionManager()

