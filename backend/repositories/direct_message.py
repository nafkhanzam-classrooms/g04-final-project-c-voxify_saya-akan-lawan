from typing import Sequence
from uuid import UUID
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from models.direct_message import DirectMessage
from repositories.base import BaseRepository


class DirectMessageRepository(BaseRepository[DirectMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(DirectMessage, session)

    async def get_chat_history(
        self, user_a: UUID, user_b: UUID, limit: int = 50, before_id: UUID | None = None
    ) -> Sequence[DirectMessage]:
        query = (
            select(DirectMessage)
            .where(
                or_(
                    and_(DirectMessage.sender_id == user_a, DirectMessage.receiver_id == user_b, DirectMessage.is_deleted_by_sender == False),
                    and_(DirectMessage.sender_id == user_b, DirectMessage.receiver_id == user_a, DirectMessage.is_deleted_by_receiver == False)
                )
            )
            .options(joinedload(DirectMessage.sender))
            .order_by(DirectMessage.created_at.desc())
            .limit(limit)
        )

        if before_id:
            timestamp_query = select(DirectMessage.created_at).where(DirectMessage.id == before_id)
            timestamp_result = await self.session.execute(timestamp_query)
            before_timestamp = timestamp_result.scalar_one_or_none()
            if before_timestamp:
                query = query.where(DirectMessage.created_at < before_timestamp)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_conversations(self, user_id: UUID) -> list[dict]:
        # This is a bit complex for a simple repository. 
        # Typically would use a raw SQL or complex group by.
        # For now, let's get the unique users we have chatted with.
        
        # Sent messages receivers
        sent_query = select(DirectMessage.receiver_id).where(DirectMessage.sender_id == user_id).distinct()
        # Received messages senders
        received_query = select(DirectMessage.sender_id).where(DirectMessage.receiver_id == user_id).distinct()
        
        sent_ids = (await self.session.execute(sent_query)).scalars().all()
        received_ids = (await self.session.execute(received_query)).scalars().all()
        
        unique_ids = list(set(sent_ids + received_ids))
        
        # For each user, we could fetch last message and unread count.
        # This is inefficient (N+1), but good for start. 
        # TODO: Optimize with a single complex query.
        
        conversations = []
        for other_id in unique_ids:
            # Last message
            last_msg_query = select(DirectMessage).where(
                or_(
                    and_(DirectMessage.sender_id == user_id, DirectMessage.receiver_id == other_id),
                    and_(DirectMessage.sender_id == other_id, DirectMessage.receiver_id == user_id)
                )
            ).order_by(DirectMessage.created_at.desc()).limit(1)
            last_msg = (await self.session.execute(last_msg_query)).scalar_one_or_none()
            
            # Unread count
            unread_query = select(func.count(DirectMessage.id)).where(
                DirectMessage.sender_id == other_id,
                DirectMessage.receiver_id == user_id,
                DirectMessage.is_read == False
            )
            unread_count = (await self.session.execute(unread_query)).scalar() or 0
            
            conversations.append({
                "other_user_id": other_id,
                "last_message": last_msg,
                "unread_count": unread_count
            })
            
        return conversations
