from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    is_online: bool
    last_seen_at: datetime

class UserShort(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
