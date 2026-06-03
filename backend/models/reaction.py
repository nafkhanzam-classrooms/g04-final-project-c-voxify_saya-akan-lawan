from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, uuid_pk

if TYPE_CHECKING:
    from models.message import Message
    from models.user import User


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[uuid_pk]
    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    emoji: Mapped[str] = mapped_column(String(50))
    
    # Relationships
    message: Mapped["Message"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_reaction_msg_user_emoji"),
    )
