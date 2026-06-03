from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, uuid_pk, timestamp

if TYPE_CHECKING:
    from models.room import Room
    from models.room_member import RoomMember
    from models.message import Message
    from models.direct_message import DirectMessage


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[timestamp]
    
    # Relationships
    created_rooms: Mapped[list["Room"]] = relationship(back_populates="creator")
    room_memberships: Mapped[list["RoomMember"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="sender")
    
    sent_direct_messages: Mapped[list["DirectMessage"]] = relationship(
        foreign_keys="DirectMessage.sender_id", back_populates="sender"
    )
    received_direct_messages: Mapped[list["DirectMessage"]] = relationship(
        foreign_keys="DirectMessage.receiver_id", back_populates="receiver"
    )
