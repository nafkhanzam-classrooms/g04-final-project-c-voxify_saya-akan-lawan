from datetime import datetime
from uuid import UUID
from repositories.direct_message import DirectMessageRepository
from repositories.user import UserRepository
from schema.direct_message import ConversationRead, DMCreate, DMRead
from schema.user import UserShort
from services.websocket_manager import manager
from utils.exceptions import AppException


class DirectMessageService:
    def __init__(self, dm_repo: DirectMessageRepository, user_repo: UserRepository):
        self.dm_repo = dm_repo
        self.user_repo = user_repo

    async def send_dm(self, sender_id: UUID, dm_in: DMCreate) -> DMRead:
        # Check if receiver exists
        receiver = await self.user_repo.get(dm_in.receiver_id)
        if not receiver:
            raise AppException("Receiver user not found.", 404)
            
        dm_data = dm_in.model_dump()
        dm_data["sender_id"] = sender_id

        new_dm = await self.dm_repo.create(**dm_data)
        await self.dm_repo.session.commit()

        # Load sender for the response
        sender = await self.user_repo.get(sender_id)
        dm_read = DMRead.model_validate(new_dm)
        dm_read.sender = UserShort.model_validate(sender)

        # Send via WebSocket to receiver
        manager.send_personal_message(
            {
                "type": "new_dm",
                "message": dm_read.model_dump(mode="json")
            },
            dm_in.receiver_id
        )
        
        manager.send_personal_message(
            {
                "type": "new_dm",
                "message": dm_read.model_dump(mode="json")
            },
            sender_id
        )

        return dm_read

    async def get_history(
        self,
        user_id: UUID,
        other_user_id: UUID,
        limit: int = 50,
        before_id: UUID | None = None,
    ) -> list[DMRead]:
        dms = await self.dm_repo.get_chat_history(
            user_id, other_user_id, limit, before_id
        )
        return [DMRead.model_validate(dm) for dm in dms]

    async def get_my_conversations(self, user_id: UUID) -> list[ConversationRead]:
        convs = await self.dm_repo.get_conversations(user_id)

        result = []
        for c in convs:
            other_user = await self.user_repo.get(c["other_user_id"])
            if not other_user:
                continue

            last_msg = c["last_message"]
            result.append(
                ConversationRead(
                    other_user=UserShort.model_validate(other_user),
                    last_message=last_msg.content if last_msg else None,
                    last_message_at=last_msg.created_at if last_msg else None,
                    unread_count=c["unread_count"],
                )
            )

        # Sort by last message time
        result.sort(key=lambda x: x.last_message_at or datetime.min, reverse=True)
        return result
