import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from db.config import DATABASE_URL
from repositories.direct_message import DirectMessageRepository
from repositories.message import MessageRepository
from repositories.room import RoomRepository
from repositories.user import UserRepository
from schema.direct_message import DMCreate
from schema.message import MessageCreate, ReactionBase
from schema.room import RoomCreate, RoomJoin
from schema.user import UserCreate, UserLogin, UserRead, UserShort
from services.auth import AuthService, get_user_from_token
from services.direct_message import DirectMessageService
from services.message import MessageService
from services.room import RoomService
from utils.exceptions import AppException

logger = logging.getLogger("voxify.dispatcher")
_PUBLIC_ACTIONS = frozenset({"auth.register", "auth.login", "auth.validate_token"})


class Dispatcher:
    @staticmethod
    @asynccontextmanager
    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_maker() as session:
                yield session
        finally:
            await engine.dispose()

    @staticmethod
    def _success(action: str, data: Any = None, message: str | None = None) -> Dict[str, Any]:
        resp: Dict[str, Any] = {"status": "success", "action": action}
        if data is not None:
            resp["data"] = data
        if message is not None:
            resp["message"] = message
        return resp

    @staticmethod
    def _error(action: str, message: str, code: int = 400) -> Dict[str, Any]:
        return {"status": "error", "action": action, "message": message, "code": code}

    async def dispatch(self, request: Dict[str, Any], client_id: Optional[UUID] = None) -> Dict[str, Any]:
        action = request.get("action")
        data = request.get("data", {})
        token = request.get("token")
        user_id = client_id
        if token and not user_id:
            user_id = await get_user_from_token(token)

        async with self._get_session() as session:
            user_repo = UserRepository(session)
            room_repo = RoomRepository(session)
            msg_repo = MessageRepository(session)
            dm_repo = DirectMessageRepository(session)

            auth_svc = AuthService(user_repo)
            room_svc = RoomService(room_repo)
            msg_svc = MessageService(msg_repo, room_repo)
            dm_svc = DirectMessageService(dm_repo, user_repo)

            try:
                if action not in _PUBLIC_ACTIONS and not user_id:
                    return self._error(action, "Unauthorized", 401)

                handler = getattr(self, f"_handle_{action.replace('.', '_')}", None)
                if not handler:
                    return self._error(action, f"Unknown action: {action}")

                return await handler(
                    action=action,
                    data=data,
                    token=token,
                    user_id=user_id,
                    auth_svc=auth_svc,
                    room_svc=room_svc,
                    msg_svc=msg_svc,
                    dm_svc=dm_svc,
                    user_repo=user_repo,
                )

            except AppException as e:
                return self._error(action, e.message, e.status_code)
            except Exception as e:
                logger.exception("Unhandled error in action '%s'", action)
                return self._error(action, str(e))

    async def _handle_auth_register(self, *, action, data, **_kw):
        user_in = UserCreate(**data)
        result = await _kw["auth_svc"].register(user_in)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_auth_login(self, *, action, data, **_kw):
        login_data = UserLogin(**data)
        result = await _kw["auth_svc"].login(login_data)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_auth_validate_token(self, *, action, token, **_kw):
        result = await _kw["auth_svc"].validate_token(token)
        return self._success(action, result.model_dump(mode="json"))
    
    async def _handle_room_create(self, *, action, data, user_id, **_kw):
        room_in = RoomCreate(**data)
        result = await _kw["room_svc"].create_room(room_in, user_id)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_room_join(self, *, action, data, user_id, **_kw):
        join_in = RoomJoin(**data)
        result = await _kw["room_svc"].join_room(join_in.invite_code, user_id)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_room_list(self, *, action, user_id, **_kw):
        result = await _kw["room_svc"].get_my_rooms(user_id)
        return self._success(action, [r.model_dump(mode="json") for r in result])

    async def _handle_room_leave(self, *, action, data, user_id, **_kw):
        room_id = UUID(data.get("room_id"))
        await _kw["room_svc"].leave_room(room_id, user_id)
        return self._success(action, message="Left room successfully")

    async def _handle_room_members(self, *, action, data, user_id, **_kw):
        room_id = UUID(data.get("room_id"))
        result = await _kw["room_svc"].get_room_members(room_id, user_id)
        return self._success(action, [m.model_dump(mode="json") for m in result])

    async def _handle_message_send(self, *, action, data, user_id, **_kw):
        room_id = UUID(data.get("room_id"))
        msg_in = MessageCreate(**data.get("message", {}))
        result = await _kw["msg_svc"].send_room_message(room_id, user_id, msg_in)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_message_history(self, *, action, data, user_id, **_kw):
        room_id = UUID(data.get("room_id"))
        limit = data.get("limit", 50)
        before_id = data.get("before_id")
        if before_id:
            before_id = UUID(before_id)
        result = await _kw["msg_svc"].get_messages(room_id, user_id, limit, before_id)
        return self._success(action, [m.model_dump(mode="json") for m in result])

    async def _handle_dm_send(self, *, action, data, user_id, **_kw):
        dm_in = DMCreate(**data)
        result = await _kw["dm_svc"].send_dm(user_id, dm_in)
        return self._success(action, result.model_dump(mode="json"))

    async def _handle_dm_conversations(self, *, action, user_id, **_kw):
        result = await _kw["dm_svc"].get_my_conversations(user_id)
        return self._success(action, [c.model_dump(mode="json") for c in result])

    async def _handle_dm_history(self, *, action, data, user_id, **_kw):
        other_user_id = UUID(data.get("other_user_id"))
        limit = data.get("limit", 50)
        before_id = data.get("before_id")
        if before_id:
            before_id = UUID(before_id)
        result = await _kw["dm_svc"].get_history(user_id, other_user_id, limit, before_id)
        return self._success(action, [m.model_dump(mode="json") for m in result])

    async def _handle_user_online_list(self, *, action, **_kw):
        online_users = await _kw["user_repo"].get_online_users()
        result = [UserShort.model_validate(u).model_dump(mode="json") for u in online_users]
        return self._success(action, result)

    async def _handle_reaction_add(self, *, action, data, user_id, **_kw):
        message_id = UUID(data.get("message_id"))
        reaction_in = ReactionBase(**data)
        await _kw["msg_svc"].add_reaction(message_id, user_id, reaction_in.emoji)
        return self._success(action, message="Reaction added")

    async def _handle_reaction_remove(self, *, action, data, user_id, **_kw):
        message_id = UUID(data.get("message_id"))
        emoji = data.get("emoji")
        removed = await _kw["msg_svc"].remove_reaction(message_id, user_id, emoji)
        if removed:
            return self._success(action, message="Reaction removed")
        return self._error(action, "Reaction not found")


dispatcher = Dispatcher()
