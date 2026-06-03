from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Common types
uuid_pk = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]
timestamp = Annotated[datetime, mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))]
updated_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    ),
]


class Base(DeclarativeBase):
    """Base class for all models."""
    id: Mapped[uuid_pk]
