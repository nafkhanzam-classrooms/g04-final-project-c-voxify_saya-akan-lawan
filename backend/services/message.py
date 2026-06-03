from uuid import UUID
from fastapi import HTTPException, status
from repositories.message import MessageRepository
from repositories.room import RoomRepository
from schema.message import MessageCreate, MessageRead, ReactionSummary
from services.websocket_manager import manager


class MessageService:
    def __init__(self, message_repo: MessageRepository, room_repo: RoomRepository):
        self.message_repo = message_repo
        self.room_repo = room_repo

    async def send_room_message(
        self, room_id: UUID, sender_id: UUID, message_in: MessageCreate
    ) -> MessageRead:
        # Check if user is member of room
        if not await self.room_repo.is_member(room_id, sender_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this room."
            )
            
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
        # We fetch the latest message for this room which should be the one we just created
        messages = await self.message_repo.get_room_messages(room_id, limit=1)
        if not messages:
            msg_read = MessageRead.model_validate(new_message)
        else:
            msg_read = MessageRead.model_validate(messages[0])

        # Broadcast to room members via WebSocket
        await manager.broadcast_to_room(
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this room."
            )
            
        messages = await self.message_repo.get_room_messages(room_id, limit, before_id)
        
        # Convert to MessageRead and handle reaction summaries
        result = []
        for msg in messages:
            msg_read = MessageRead.model_validate(msg)
            # Reaction summary logic
            summaries = {}
            for r in msg.reactions:
                if r.emoji not in summaries:
                    summaries[r.emoji] = ReactionSummary(emoji=r.emoji, count=0, me=False)
                summaries[r.emoji].count += 1
                if r.user_id == user_id:
                    summaries[r.emoji].me = True
            
            msg_read.reactions = list(summaries.values())
            result.append(msg_read)
            
        return result
