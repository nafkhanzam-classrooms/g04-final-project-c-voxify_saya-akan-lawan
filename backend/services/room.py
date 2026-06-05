import random
import string
from uuid import UUID

from repositories.room import RoomRepository
from schema.room import RoomCreate, RoomRead
from services.exceptions import AppException


class RoomService:
    def __init__(self, room_repo: RoomRepository):
        self.room_repo = room_repo

    def _generate_invite_code(self, length: int = 8) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    async def create_room(self, room_in: RoomCreate, creator_id: UUID) -> RoomRead:
        invite_code = self._generate_invite_code()

        # Ensure invite code is unique
        while await self.room_repo.get_by_invite_code(invite_code):
            invite_code = self._generate_invite_code()

        room_data = room_in.model_dump()
        room_data.update({"invite_code": invite_code, "created_by": creator_id})

        new_room = await self.room_repo.create(**room_data)

        # Add creator as owner
        await self.room_repo.add_member(new_room.id, creator_id, role="owner")

        await self.room_repo.session.commit()
        return RoomRead.model_validate(new_room)

    async def join_room(self, invite_code: str, user_id: UUID) -> RoomRead:
        room = await self.room_repo.get_by_invite_code(invite_code)
        if not room:
            raise AppException(
                status=404,
                message="Room not found with the provided invite code.",
            )

        if await self.room_repo.is_member(room.id, user_id):
            raise AppException(
                status=400,
                message="You are already a member of this room.",
            )

        await self.room_repo.add_member(room.id, user_id)
        await self.room_repo.session.commit()

        return RoomRead.model_validate(room)

    async def get_my_rooms(self, user_id: UUID) -> list[RoomRead]:
        rooms = await self.room_repo.get_user_rooms(user_id)
        return [RoomRead.model_validate(r) for r in rooms]
