"""Secret model - secure key-value store for credentials and API keys."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class Secret(TimestampMixin, Base):
    """
    A single secret entry (e.g. API credential).

    Keys are seeded by migration; only values can be updated at runtime.
    Values are never exposed through MCP tools — only internal code reads them.
    """

    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Unique secret key (e.g. "EDUPAGE_PASSWORD")
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Secret value (nullable — NULL means not yet configured)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human-readable description
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    def __repr__(self) -> str:
        return f"<Secret(key={self.key!r}, is_set={self.value is not None})>"
