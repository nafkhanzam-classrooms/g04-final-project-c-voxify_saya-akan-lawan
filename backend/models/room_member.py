from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, timestamp

if TYPE_CHECKING:
    from models.room import Room
    from models.user import User


class RoomMember(Base):
    __tablename__ = "room_members"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"))
    role: Mapped[str] = mapped_column(String(20), default="member")

    joined_at: Mapped[timestamp]
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="room_memberships")
    room: Mapped["Room"] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("user_id", "room_id", name="uq_room_member_user_room"),
    )
