from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from app.core.database import Base


def utc_now() -> datetime:
    """Returns current naive UTC timestamp for database storage consistency."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """Standard timestamp mixin applying UTC created_at and updated_at."""

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
