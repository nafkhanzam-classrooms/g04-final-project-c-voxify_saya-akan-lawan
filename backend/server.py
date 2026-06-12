import socket
import threading
import asyncio
from typing import Optional
from uuid import UUID

from utils.protocol import receive_message, send_message
from dispatcher import dispatcher, get_user_from_token
from services.websocket_manager import manager

class ThreadedTCPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.is_running = True
        print(f"[*] Raw TCP Server listening on {self.host}:{self.port}")

        try:
            while self.is_running:
                client_sock, address = self.server_socket.accept()
                print(f"[*] Accepted connection from {address[0]}:{address[1]}")
                
                # Start a new thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_sock,)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[*] Shutting down server...")
        finally:
            self.stop()

    def handle_client(self, client_sock: socket.socket):
        user_id: Optional[UUID] = None
        # Create a dedicated event loop for this thread so all async calls
        # (and the SQLAlchemy engine's connection pool) share the same loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Timeout 5 menit: thread tidak akan hang selamanya jika klien diam.
        client_sock.settimeout(300)

        try:
            while True:
                request = receive_message(client_sock)
                if request is None:
                    break  # Client disconnected, timeout, atau payload invalid

                action = request.get("action")
                print(f"[>] Received action: {action} from user {user_id or 'anonymous'}")

                if action == "auth.login":
                    response = loop.run_until_complete(dispatcher.dispatch(request))
                    if response["status"] == "success":
                        new_user_id = UUID(response["data"]["user"]["id"])
                        # Jika user sebelumnya sudah login, putus koneksi lamanya
                        if user_id and user_id != new_user_id:
                            manager.disconnect(user_id)
                        user_id = new_user_id
                        manager.connect(user_id, client_sock)
                        # Broadcast user online
                        manager.broadcast_global({
                            "type": "user_presence",
                            "user_id": str(user_id),
                            "is_online": True,
                            "username": response["data"]["user"]["username"],
                            "display_name": response["data"]["user"].get("display_name")
                        })
                    send_message(client_sock, response)
                    print(f"[<] Response: {response.get('status')} for {action}")

                elif action == "room.join_socket":
                    room_id = request.get("data", {}).get("room_id")
                    if user_id and room_id:
                        manager.join_room(UUID(room_id), user_id)
                        send_message(client_sock, {"status": "success", "message": "Joined room socket"})

                elif action == "room.leave_socket":
                    room_id = request.get("data", {}).get("room_id")
                    if user_id and room_id:
                        manager.leave_room(UUID(room_id), user_id)
                        send_message(client_sock, {"status": "success", "message": "Left room socket"})

                else:
                    response = loop.run_until_complete(dispatcher.dispatch(request, client_id=user_id))
                    print(f"[<] Response: {response.get('status')} for {action}")
                    send_message(client_sock, response)

        except Exception as e:
            print(f"[!] Error handling client: {e}")
        finally:
            if user_id:
                manager.disconnect(user_id)
                # Set user offline di database
                try:
                    loop.run_until_complete(self._set_user_offline(user_id))
                except Exception as e:
                    print(f"[!] Failed to set user offline: {e}")
                
                # Broadcast user offline
                manager.broadcast_global({
                    "type": "user_presence",
                    "user_id": str(user_id),
                    "is_online": False
                })
            loop.close()
            client_sock.close()
            print("[*] Client disconnected")

    async def _set_user_offline(self, user_id: UUID):
        """Helper async untuk update status online user saat disconnect."""
        from sqlalchemy.pool import NullPool
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from db.config import DATABASE_URL
        from repositories.user import UserRepository

        engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_maker() as session:
                user_repo = UserRepository(session)
                await user_repo.update_online_status(user_id, False)
                await session.commit()
        finally:
            await engine.dispose()

    def stop(self):
        self.is_running = False
        self.server_socket.close()

if __name__ == "__main__":
    server = ThreadedTCPServer()
    server.start()
