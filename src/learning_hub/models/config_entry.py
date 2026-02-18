"""ConfigEntry model - centralized key-value configuration store."""

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class ConfigEntry(TimestampMixin, Base):
    """
    A single configuration entry.

    Stores key-value pairs for all configurable parameters.
    Values are stored as text (JSON for complex types, plain text for scalars).
    Keys are seeded by migration; only values can be updated at runtime.
    """

    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Unique config key (e.g. "GRADE_MINUTES_MAP")
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Value stored as text (JSON for dicts/lists, plain for strings/ints)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human-readable description
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Whether this config must be set before certain workflows can operate
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigEntry(key={self.key!r}, value={self.value!r})>"
