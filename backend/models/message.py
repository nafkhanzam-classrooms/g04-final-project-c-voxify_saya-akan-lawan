from typing import TYPE_CHECKING, Optional, Any
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, uuid_pk, timestamp

if TYPE_CHECKING:
    from models.user import User
    from models.room import Room
    from models.reaction import Reaction


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid_pk]
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"))
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    content: Mapped[Optional[str]] = mapped_column(String)
    file_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[timestamp]
    
    # Relationships
    room: Mapped["Room"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages")
    reactions: Mapped[list["Reaction"]] = relationship(back_populates="message")
