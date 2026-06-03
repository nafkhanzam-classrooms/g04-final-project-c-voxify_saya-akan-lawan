from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from schema.user import UserShort

class ReactionBase(BaseModel):
    emoji: str

class ReactionRead(ReactionBase):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID

class ReactionSummary(BaseModel):
    emoji: str
    count: int
    me: bool = False

class MessageBase(BaseModel):
    content: Optional[str] = None
    file_metadata: Optional[dict[str, Any]] = None

class MessageCreate(MessageBase):
    pass

class MessageRead(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_id: UUID
    created_at: datetime
    sender: UserShort
    reactions: List[ReactionSummary] = []
