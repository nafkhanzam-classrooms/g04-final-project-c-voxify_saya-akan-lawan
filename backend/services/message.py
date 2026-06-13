from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.message import Message
from repositories.message import MessageRepository
from repositories.room import RoomRepository
from schema.message import MessageCreate, MessageRead, ReactionSummary
from services.websocket_manager import manager
from utils.exceptions import AppException


class MessageService:
    def __init__(self, message_repo: MessageRepository, room_repo: RoomRepository):
        self.message_repo = message_repo
        self.room_repo = room_repo

    # ── Reaction Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _build_reaction_summaries(
        reactions, viewer_id: UUID | None = None
    ) -> list[ReactionSummary]:
        """Aggregate raw Reaction ORM objects into a list of ReactionSummary."""
        summaries: dict[str, ReactionSummary] = {}
        for r in reactions:
            if r.emoji not in summaries:
                summaries[r.emoji] = ReactionSummary(emoji=r.emoji, count=0, me=False)
            summaries[r.emoji].count += 1
            if viewer_id and r.user_id == viewer_id:
                summaries[r.emoji].me = True
        return list(summaries.values())

    @staticmethod
    def _message_to_read(msg: Message, viewer_id: UUID | None = None) -> MessageRead:
        """Convert a Message ORM object (with eager-loaded sender & reactions)
        into a MessageRead schema."""
        reaction_summaries = MessageService._build_reaction_summaries(
            msg.reactions, viewer_id
        )
        msg_data = {
            "id": msg.id,
            "room_id": msg.room_id,
            "content": msg.content,
            "file_metadata": msg.file_metadata,
            "created_at": msg.created_at,
            "sender": msg.sender,
            "reactions": reaction_summaries,
        }
        return MessageRead.model_validate(msg_data)

    # ── Reactions ───────────────────────────────────────────────────────────

    async def add_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> None:
        await self.message_repo.add_reaction(message_id, user_id, emoji)
        await self.message_repo.session.commit()
        await self._broadcast_reaction_update(message_id)

    async def remove_reaction(self, message_id: UUID, user_id: UUID, emoji: str) -> bool:
        removed = await self.message_repo.remove_reaction(message_id, user_id, emoji)
        if removed:
            await self.message_repo.session.commit()
            await self._broadcast_reaction_update(message_id)
        return removed

    async def _broadcast_reaction_update(self, message_id: UUID) -> None:
        """Reload the message's reactions and broadcast the update to the room."""
        query = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.reactions))
        )
        result = await self.message_repo.session.execute(query)
        msg = result.scalar_one_or_none()
        if msg:
            summaries = self._build_reaction_summaries(msg.reactions)
            manager.broadcast_to_room(
                msg.room_id,
                {
                    "type": "reaction_update",
                    "room_id": str(msg.room_id),
                    "message_id": str(message_id),
                    "reactions": [s.model_dump(mode="json") for s in summaries],
                },
            )

    # ── Room Messages ───────────────────────────────────────────────────────

    async def send_room_message(
        self, room_id: UUID, sender_id: UUID, message_in: MessageCreate
    ) -> MessageRead:
        if not await self.room_repo.is_member(room_id, sender_id):
            raise AppException("You are not a member of this room.", 403)

        message_data = message_in.model_dump()
        message_data.update({"room_id": room_id, "sender_id": sender_id})

        new_message = await self.message_repo.create(**message_data)
        await self.room_repo.update(room_id, last_message_at=new_message.created_at)
        await self.message_repo.session.commit()

        # Reload with sender + reactions eager-loaded
        messages = await self.message_repo.get_room_messages(room_id, limit=1)
        if not messages:
            msg_read = MessageRead.model_validate(new_message)
        else:
            msg_read = self._message_to_read(messages[0], viewer_id=sender_id)

        # Broadcast to room members
        manager.broadcast_to_room(
            room_id,
            {
                "type": "new_message",
                "room_id": str(room_id),
                "message": msg_read.model_dump(mode="json"),
            },
        )
        return msg_read

    async def get_messages(
        self,
        room_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: UUID | None = None,
    ) -> list[MessageRead]:
        if not await self.room_repo.is_member(room_id, user_id):
            raise AppException("You are not a member of this room.", 403)

        messages = await self.message_repo.get_room_messages(room_id, limit, before_id)
        return [self._message_to_read(msg, viewer_id=user_id) for msg in messages]
