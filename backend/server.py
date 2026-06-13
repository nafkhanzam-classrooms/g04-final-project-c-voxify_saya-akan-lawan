import asyncio
import logging
import socket
import threading
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from db.config import DATABASE_URL
from dispatcher import dispatcher
from repositories.user import UserRepository
from services.auth import get_user_from_token
from services.websocket_manager import manager
from utils.protocol import receive_message, send_message

# ── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("voxify.server")


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
        logger.info("Raw TCP Server listening on %s:%d", self.host, self.port)

        try:
            while self.is_running:
                client_sock, address = self.server_socket.accept()
                logger.info("Accepted connection from %s:%d", address[0], address[1])

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock,),
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self.stop()


    def handle_client(self, client_sock: socket.socket):
        user_id: Optional[UUID] = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 5-minute timeout so idle threads don't hang forever
        client_sock.settimeout(300)

        try:
            while True:
                request = receive_message(client_sock)
                if request is None:
                    break

                action = request.get("action")
                logger.info("← Received '%s' from user %s", action, user_id or "anonymous")
                if action in ("auth.login", "auth.validate_token"):
                    response = loop.run_until_complete(dispatcher.dispatch(request))
                    if response.get("status") == "success":
                        user_id = self._handle_auth_success(response, user_id, client_sock)
                    send_message(client_sock, response)

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
                    response = loop.run_until_complete(
                        dispatcher.dispatch(request, client_id=user_id)
                    )
                    send_message(client_sock, response)

                logger.info("→ Processed '%s'", action)

        except Exception as e:
            logger.exception("Error handling client: %s", e)
        finally:
            if user_id:
                manager.disconnect(user_id)
                self._set_user_offline(loop, user_id)
                manager.broadcast_global({
                    "type": "user_presence",
                    "user_id": str(user_id),
                    "is_online": False,
                })
            loop.close()
            client_sock.close()
            logger.info("Client disconnected (user=%s)", user_id or "anonymous")

    @staticmethod
    def _handle_auth_success(
        response: dict, old_user_id: Optional[UUID], client_sock: socket.socket
    ) -> UUID:
        new_user_id = UUID(response["data"]["user"]["id"])

        if old_user_id and old_user_id != new_user_id:
            manager.disconnect(old_user_id)

        manager.connect(new_user_id, client_sock)
        manager.broadcast_global({
            "type": "user_presence",
            "user_id": str(new_user_id),
            "is_online": True,
            "username": response["data"]["user"]["username"],
            "display_name": response["data"]["user"].get("display_name")
,
        })
        return new_user_id

    @staticmethod
    def _set_user_offline(loop: asyncio.AbstractEventLoop, user_id: UUID):
        async def _do():
            engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
            session_maker = async_sessionmaker(engine, expire_on_commit=False)
            try:
                async with session_maker() as session:
                    user_repo = UserRepository(session)
                    await user_repo.update_online_status(user_id, False)
                    await session.commit()
            finally:
                await engine.dispose()

        try:
            loop.run_until_complete(_do())
        except Exception as e:
            logger.error("Failed to set user %s offline: %s", user_id, e)

    def stop(self):
        self.is_running = False
        self.server_socket.close()


if __name__ == "__main__":
    server = ThreadedTCPServer()
    server.start()
