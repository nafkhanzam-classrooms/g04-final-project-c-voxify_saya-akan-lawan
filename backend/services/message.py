from uuid import UUID
from repositories.message import MessageRepository
from repositories.room import RoomRepository
from schema.message import MessageCreate, MessageRead, ReactionSummary
from services.websocket_manager import manager
from utils.exceptions import AppException


class MessageService:
    def __init__(self, message_repo: MessageRepository, room_repo: RoomRepository):
        self.message_repo = message_repo
        self.room_repo = room_repo

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> None:
        await self.message_repo.add_reaction(message_id, user_id, emoji)
        await self.message_repo.session.commit()
        
        # Broadcast reaction update to the room
        await self._broadcast_reaction_update(message_id)

    async def remove_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> bool:
        removed = await self.message_repo.remove_reaction(message_id, user_id, emoji)
        if removed:
            await self.message_repo.session.commit()
            # Broadcast reaction update to the room
            await self._broadcast_reaction_update(message_id)
        return removed

    async def _broadcast_reaction_update(self, message_id: UUID) -> None:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from models.message import Message
        
        # Reload message with its reactions
        query = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.reactions))
        )
        result = await self.message_repo.session.execute(query)
        msg = result.scalar_one_or_none()
        if msg:
            summaries = {}
            for r in msg.reactions:
                if r.emoji not in summaries:
                    summaries[r.emoji] = ReactionSummary(emoji=r.emoji, count=0, me=False)
                summaries[r.emoji].count += 1

            manager.broadcast_to_room(
                msg.room_id,
                {
                    "type": "reaction_update",
                    "room_id": str(msg.room_id),
                    "message_id": str(message_id),
                    "reactions": [s.model_dump(mode="json") for s in summaries.values()]
                }
            )

    async def send_room_message(
        self, room_id: UUID, sender_id: UUID, message_in: MessageCreate
    ) -> MessageRead:
        # Check if user is member of room
        if not await self.room_repo.is_member(room_id, sender_id):
            raise AppException("You are not a member of this room.", 403)
            
        message_data = message_in.model_dump()
        message_data.update({
            "room_id": room_id,
            "sender_id": sender_id
        })
        
        new_message = await self.message_repo.create(**message_data)
        
        # Update room last_message_at
        await self.room_repo.update(room_id, last_message_at=new_message.created_at)
        
        await self.message_repo.session.commit()
        
        # Reload message with sender and reactions to match MessageRead
        messages = await self.message_repo.get_room_messages(room_id, limit=1)
        if not messages:
            msg_read = MessageRead.model_validate(new_message)
        else:
            # Handle reaction summary mapping
            msg = messages[0]
            summaries = {}
            for r in msg.reactions:
                if r.emoji not in summaries:
                    summaries[r.emoji] = ReactionSummary(emoji=r.emoji, count=0, me=False)
                summaries[r.emoji].count += 1
                if r.user_id == sender_id:
                    summaries[r.emoji].me = True
            
            msg_data = {
                "id": msg.id,
                "room_id": msg.room_id,
                "content": msg.content,
                "file_metadata": msg.file_metadata,
                "created_at": msg.created_at,
                "sender": msg.sender,
                "reactions": list(summaries.values())
            }
            msg_read = MessageRead.model_validate(msg_data)

        # Broadcast to room members via WebSocket
        manager.broadcast_to_room(
            room_id, 
            {
                "type": "new_message",
                "room_id": str(room_id),
                "message": msg_read.model_dump(mode="json")
            }
        )
        
        return msg_read

    async def get_messages(
        self, room_id: UUID, user_id: UUID, limit: int = 50, before_id: UUID | None = None
    ) -> list[MessageRead]:
        if not await self.room_repo.is_member(room_id, user_id):
            raise AppException("You are not a member of this room.", 403)
            
        messages = await self.message_repo.get_room_messages(room_id, limit, before_id)
        
        # Convert to MessageRead and handle reaction summaries
        result = []
        for msg in messages:
            # Reaction summary logic
            summaries = {}
            for r in msg.reactions:
                if r.emoji not in summaries:
                    summaries[r.emoji] = ReactionSummary(emoji=r.emoji, count=0, me=False)
                summaries[r.emoji].count += 1
                if r.user_id == user_id:
                    summaries[r.emoji].me = True
            
            # Map values manually first so Pydantic does not fail on unmapped reactions
            msg_data = {
                "id": msg.id,
                "room_id": msg.room_id,
                "content": msg.content,
                "file_metadata": msg.file_metadata,
                "created_at": msg.created_at,
                "sender": msg.sender,  # UserShort can validate from attributes
                "reactions": list(summaries.values())
            }
            msg_read = MessageRead.model_validate(msg_data)
            result.append(msg_read)
            
        return result
