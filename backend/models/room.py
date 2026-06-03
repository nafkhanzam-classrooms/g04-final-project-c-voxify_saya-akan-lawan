from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, uuid_pk

if TYPE_CHECKING:
    from models.user import User
    from models.room_member import RoomMember
    from models.message import Message


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(String(100))
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    creator: Mapped["User"] = relationship(back_populates="created_rooms")
    members: Mapped[list["RoomMember"]] = relationship(back_populates="room")
    messages: Mapped[list["Message"]] = relationship(back_populates="room")
