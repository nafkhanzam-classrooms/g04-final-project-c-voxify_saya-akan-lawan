from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_session
from routers.deps import get_current_user
from repositories.room import RoomRepository
from services.room import RoomService
from schema.room import RoomCreate, RoomRead, RoomJoin
from schema.user import UserRead
from schema.base import BaseResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])

async def get_room_repository(session: Annotated[AsyncSession, Depends(get_async_session)]) -> RoomRepository:
    return RoomRepository(session)

async def get_room_service(room_repo: Annotated[RoomRepository, Depends(get_room_repository)]) -> RoomService:
    return RoomService(room_repo)

@router.post("", response_model=BaseResponse[RoomRead], status_code=status.HTTP_201_CREATED)
async def create_room(
    room_in: RoomCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)]
):
    room = await room_service.create_room(room_in, current_user.id)
    return BaseResponse(data=room, message="Room created successfully")

@router.get("", response_model=BaseResponse[List[RoomRead]])
async def list_joined_rooms(
    current_user: Annotated[UserRead, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)]
):
    rooms = await room_service.get_my_rooms(current_user.id)
    return BaseResponse(data=rooms)

@router.post("/join", response_model=BaseResponse[RoomRead])
async def join_room(
    join_in: RoomJoin,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)]
):
    room = await room_service.join_room(join_in.invite_code, current_user.id)
    return BaseResponse(data=room, message="Joined room successfully")
