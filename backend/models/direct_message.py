from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, timestamp

if TYPE_CHECKING:
    from models.user import User


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    content: Mapped[Optional[str]] = mapped_column(String)
    file_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    is_deleted_by_sender: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted_by_receiver: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[timestamp]

    # Relationships
    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id], back_populates="sent_direct_messages"
    )
    receiver: Mapped["User"] = relationship(
        foreign_keys=[receiver_id], back_populates="received_direct_messages"
    )
