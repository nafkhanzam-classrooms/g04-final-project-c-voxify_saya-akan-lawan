from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.message import Message
    from models.room_member import RoomMember
    from models.user import User


class Room(Base):
    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(100))
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    creator: Mapped["User"] = relationship(back_populates="created_rooms")
    members: Mapped[list["RoomMember"]] = relationship(back_populates="room")
    messages: Mapped[list["Message"]] = relationship(back_populates="room")
