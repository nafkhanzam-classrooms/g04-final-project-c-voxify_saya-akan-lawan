from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class RoomBase(BaseModel):
    name: str
    topic: Optional[str] = None
    avatar_url: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class RoomRead(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invite_code: str
    created_by: UUID
    is_active: bool
    last_message_at: datetime

class RoomJoin(BaseModel):
    invite_code: str

class RoomMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    room_id: UUID
    role: str
    joined_at: datetime
