from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from models.room import Room
from models.room_member import RoomMember
from repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(Room, session)

    async def get_by_invite_code(self, invite_code: str) -> Room | None:
        query = select(Room).where(Room.invite_code == invite_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_rooms(self, user_id: UUID) -> list[Room]:
        query = (
            select(Room)
            .join(RoomMember)
            .where(RoomMember.user_id == user_id)
            .order_by(Room.last_message_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_member(self, room_id: UUID, user_id: UUID, role: str = "member") -> RoomMember:
        member = RoomMember(room_id=room_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        return member

    async def is_member(self, room_id: UUID, user_id: UUID) -> bool:
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def remove_member(self, room_id: UUID, user_id: UUID) -> bool:
        from sqlalchemy import delete
        query = delete(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def get_room_members(self, room_id: UUID) -> list[RoomMember]:
        query = (
            select(RoomMember)
            .where(RoomMember.room_id == room_id)
            .options(joinedload(RoomMember.user))
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

