from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.message import Message
from models.reaction import Reaction
from repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def get_room_messages(
        self, room_id: UUID, limit: int = 50, before_id: UUID | None = None
    ) -> Sequence[Message]:
        query = (
            select(Message)
            .where(Message.room_id == room_id, Message.is_deleted == False)
            .options(
                joinedload(Message.sender),
                selectinload(Message.reactions)
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        if before_id:
            # Subquery to get the timestamp of the before_id message
            # Or simpler if IDs are sequential/sortable, but created_at is safer
            timestamp_query = select(Message.created_at).where(Message.id == before_id)
            timestamp_result = await self.session.execute(timestamp_query)
            before_timestamp = timestamp_result.scalar_one_or_none()
            
            if before_timestamp:
                query = query.where(Message.created_at < before_timestamp)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> Reaction:
        reaction = Reaction(message_id=message_id, user_id=user_id, emoji=emoji)
        self.session.add(reaction)
        await self.session.flush()
        return reaction

    async def remove_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> bool:
        from sqlalchemy import delete
        query = delete(Reaction).where(
            Reaction.message_id == message_id,
            Reaction.user_id == user_id,
            Reaction.emoji == emoji
        )
        result = await self.session.execute(query)
        return result.rowcount > 0
