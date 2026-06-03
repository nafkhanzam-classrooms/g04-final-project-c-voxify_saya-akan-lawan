from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_session
from routers.deps import get_current_user
from routers.rooms import get_room_repository
from repositories.message import MessageRepository
from repositories.room import RoomRepository
from services.message import MessageService
from schema.message import MessageCreate, MessageRead
from schema.user import UserRead
from schema.base import BaseResponse

router = APIRouter(tags=["Messages"])

async def get_message_repository(session: Annotated[AsyncSession, Depends(get_async_session)]) -> MessageRepository:
    return MessageRepository(session)

async def get_message_service(
    msg_repo: Annotated[MessageRepository, Depends(get_message_repository)],
    room_repo: Annotated[RoomRepository, Depends(get_room_repository)]
) -> MessageService:
    return MessageService(msg_repo, room_repo)

@router.post("/rooms/{room_id}/messages", response_model=BaseResponse[MessageRead], status_code=status.HTTP_201_CREATED)
async def send_room_message(
    room_id: UUID,
    message_in: MessageCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    message_service: Annotated[MessageService, Depends(get_message_service)]
):
    message = await message_service.send_room_message(room_id, current_user.id, message_in)
    return BaseResponse(data=message, message="Message sent")

@router.get("/rooms/{room_id}/messages", response_model=BaseResponse[List[MessageRead]])
async def get_room_messages(
    room_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[UUID] = None
):
    messages = await message_service.get_messages(room_id, current_user.id, limit, before_id)
    return BaseResponse(data=messages)
