from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_session
from routers.deps import get_current_user, get_user_repository
from repositories.direct_message import DirectMessageRepository
from repositories.user import UserRepository
from services.direct_message import DirectMessageService
from schema.direct_message import DMCreate, DMRead, ConversationRead
from schema.user import UserRead
from schema.base import BaseResponse

router = APIRouter(prefix="/dms", tags=["Direct Messages"])

async def get_dm_repository(session: Annotated[AsyncSession, Depends(get_async_session)]) -> DirectMessageRepository:
    return DirectMessageRepository(session)

async def get_dm_service(
    dm_repo: Annotated[DirectMessageRepository, Depends(get_dm_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> DirectMessageService:
    return DirectMessageService(dm_repo, user_repo)

@router.post("", response_model=BaseResponse[DMRead], status_code=status.HTTP_201_CREATED)
async def send_dm(
    dm_in: DMCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    dm_service: Annotated[DirectMessageService, Depends(get_dm_service)]
):
    dm = await dm_service.send_dm(current_user.id, dm_in)
    return BaseResponse(data=dm, message="Message sent")

@router.get("/conversations", response_model=BaseResponse[List[ConversationRead]])
async def list_conversations(
    current_user: Annotated[UserRead, Depends(get_current_user)],
    dm_service: Annotated[DirectMessageService, Depends(get_dm_service)]
):
    convs = await dm_service.get_my_conversations(current_user.id)
    return BaseResponse(data=convs)

@router.get("/{other_user_id}", response_model=BaseResponse[List[DMRead]])
async def get_dm_history(
    other_user_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    dm_service: Annotated[DirectMessageService, Depends(get_dm_service)],
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[UUID] = None
):
    history = await dm_service.get_history(current_user.id, other_user_id, limit, before_id)
    return BaseResponse(data=history)
