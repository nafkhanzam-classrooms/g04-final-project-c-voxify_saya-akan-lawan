from typing import Any, Dict, Optional
from uuid import UUID

from jose import jwt, JWTError
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from services.security import SECRET_KEY, ALGORITHM
from db.config import DATABASE_URL
from repositories.user import UserRepository
from repositories.room import RoomRepository
from repositories.message import MessageRepository
from repositories.direct_message import DirectMessageRepository
from services.auth import AuthService
from services.room import RoomService
from services.message import MessageService
from services.direct_message import DirectMessageService
from schema.user import UserCreate, UserLogin, UserRead, UserShort
from schema.room import RoomCreate, RoomJoin, RoomMemberRead
from schema.message import MessageCreate, ReactionBase
from schema.direct_message import DMCreate
from utils.exceptions import AppException


async def get_user_from_token(token: str) -> Optional[UUID]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return UUID(str(user_id))
    except (JWTError, ValueError):
        return None
    return None


class Dispatcher:
    async def dispatch(self, request: Dict[str, Any], client_id: Optional[UUID] = None) -> Dict[str, Any]:
        action = request.get("action")
        data = request.get("data", {})
        token = request.get("token")

        user_id = client_id
        if token and not user_id:
            user_id = await get_user_from_token(token)

        # Buat engine baru per dispatch agar selalu terikat ke event loop thread saat ini.
        # NullPool = tidak ada connection pool, koneksi langsung dibuka dan ditutup.
        # Dispose wajib dipanggil di finally agar resource DB tidak bocor.
        engine = create_async_engine(DATABASE_URL, echo=True, poolclass=NullPool)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_maker() as session:
                # Init Repos
                user_repo = UserRepository(session)
                room_repo = RoomRepository(session)
                msg_repo = MessageRepository(session)
                dm_repo = DirectMessageRepository(session)

                # Init Services
                auth_service = AuthService(user_repo)
                room_service = RoomService(room_repo)
                msg_service = MessageService(msg_repo, room_repo)
                dm_service = DirectMessageService(dm_repo, user_repo)

                try:
                    # ── 1. Auth Actions (tidak butuh autentikasi) ──────────────
                    if action == "auth.register":
                        user_in = UserCreate(**data)
                        result = await auth_service.register(user_in)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "auth.login":
                        login_data = UserLogin(**data)
                        result = await auth_service.login(login_data)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "auth.validate_token":
                        # Validate token and return user data for session restore
                        if not token:
                            return {"status": "error", "action": action, "message": "No token provided", "code": 401}
                        validated_user_id = await get_user_from_token(token)
                        if not validated_user_id:
                            return {"status": "error", "action": action, "message": "Invalid or expired token", "code": 401}
                        user = await user_repo.get(validated_user_id)
                        if not user:
                            return {"status": "error", "action": action, "message": "User not found", "code": 404}
                        # Mark user online in DB (same as login)
                        await user_repo.update_online_status(user.id, True)
                        await session.commit()
                        # Re-fetch after update so is_online=True is reflected in response
                        user = await user_repo.get(validated_user_id)
                        user_data = UserRead.model_validate(user)
                        return {"status": "success", "action": action, "data": {
                            "access_token": token,
                            "token_type": "bearer",
                            "user": user_data.model_dump(mode="json")
                        }}

                    # ── Guard: semua action di bawah butuh autentikasi ─────────
                    elif not user_id:
                        return {"status": "error", "action": action, "message": "Unauthorized", "code": 401}

                    # ── 2. Room Actions ────────────────────────────────────────
                    elif action == "room.create":
                        room_in = RoomCreate(**data)
                        result = await room_service.create_room(room_in, user_id)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "room.join":
                        join_in = RoomJoin(**data)
                        result = await room_service.join_room(join_in.invite_code, user_id)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "room.list":
                        result = await room_service.get_my_rooms(user_id)
                        return {"status": "success", "action": action, "data": [r.model_dump(mode="json") for r in result]}

                    elif action == "room.leave":
                        room_id = UUID(data.get("room_id"))
                        await room_service.leave_room(room_id, user_id)
                        return {"status": "success", "action": action, "message": "Left room successfully"}

                    elif action == "room.members":
                        room_id = UUID(data.get("room_id"))
                        result = await room_service.get_room_members(room_id, user_id)
                        return {"status": "success", "action": action, "data": [m.model_dump(mode="json") for m in result]}

                    # ── 3. Message Actions ─────────────────────────────────────
                    elif action == "message.send":
                        room_id = UUID(data.get("room_id"))
                        msg_in = MessageCreate(**data.get("message", {}))
                        result = await msg_service.send_room_message(room_id, user_id, msg_in)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "message.history":
                        room_id = UUID(data.get("room_id"))
                        limit = data.get("limit", 50)
                        before_id = data.get("before_id")
                        if before_id:
                            before_id = UUID(before_id)
                        result = await msg_service.get_messages(room_id, user_id, limit, before_id)
                        return {"status": "success", "action": action, "data": [m.model_dump(mode="json") for m in result]}

                    # ── 4. DM Actions ──────────────────────────────────────────
                    elif action == "dm.send":
                        dm_in = DMCreate(**data)
                        result = await dm_service.send_dm(user_id, dm_in)
                        return {"status": "success", "action": action, "data": result.model_dump(mode="json")}

                    elif action == "dm.conversations":
                        result = await dm_service.get_my_conversations(user_id)
                        return {"status": "success", "action": action, "data": [c.model_dump(mode="json") for c in result]}

                    elif action == "dm.history":
                        other_user_id = UUID(data.get("other_user_id"))
                        limit = data.get("limit", 50)
                        before_id = data.get("before_id")
                        if before_id:
                            before_id = UUID(before_id)
                        result = await dm_service.get_history(user_id, other_user_id, limit, before_id)
                        return {"status": "success", "action": action, "data": [m.model_dump(mode="json") for m in result]}

                    # ── 5. User Actions ────────────────────────────────────────
                    elif action == "user.online_list":
                        online_users = await user_repo.get_online_users()
                        result = [UserShort.model_validate(u).model_dump(mode="json") for u in online_users]
                        return {"status": "success", "action": action, "data": result}

                    # ── 6. Reaction Actions ────────────────────────────────────
                    elif action == "reaction.add":
                        message_id = UUID(data.get("message_id"))
                        reaction_in = ReactionBase(**data)
                        await msg_service.add_reaction(message_id, user_id, reaction_in.emoji)
                        return {"status": "success", "action": action, "message": "Reaction added"}

                    elif action == "reaction.remove":
                        message_id = UUID(data.get("message_id"))
                        emoji = data.get("emoji")
                        removed = await msg_service.remove_reaction(message_id, user_id, emoji)
                        if removed:
                            return {"status": "success", "action": action, "message": "Reaction removed"}
                        return {"status": "error", "action": action, "message": "Reaction not found"}

                    else:
                        return {"status": "error", "action": action, "message": f"Unknown action: {action}"}

                except AppException as e:
                    return {"status": "error", "action": action, "message": e.message, "code": e.status_code}
                except Exception as e:
                    return {"status": "error", "action": action, "message": str(e)}

        finally:
            # Wajib: buang engine agar koneksi DB dan resource memori dibebaskan
            await engine.dispose()


dispatcher = Dispatcher()

