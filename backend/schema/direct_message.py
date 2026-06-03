from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from schema.user import UserShort

class DMBase(BaseModel):
    content: Optional[str] = None
    file_metadata: Optional[dict[str, Any]] = None

class DMCreate(DMBase):
    receiver_id: UUID

class DMRead(DMBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sender: UserShort
    receiver_id: UUID
    is_read: bool
    created_at: datetime

class ConversationRead(BaseModel):
    other_user: UserShort
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
