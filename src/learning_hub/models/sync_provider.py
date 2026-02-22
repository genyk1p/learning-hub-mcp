"""SyncProvider model - external sync services for grades and homeworks."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.school import School


class SyncProvider(TimestampMixin, Base):
    """
    External service that syncs grades/homeworks automatically.

    Each provider links to at most one school (1:1).
    Providers are seeded by migration; only is_active and school_id
    are updated at runtime via MCP tools.
    """

    __tablename__ = "sync_providers"
    __table_args__ = (
        CheckConstraint(
            "is_active = 0 OR school_id IS NOT NULL",
            name="ck_active_requires_school",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Provider type from enum (e.g. "edupage")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Human-readable name (e.g. "EduPage")
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Whether this provider is currently active
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Linked school (1:1, nullable on both sides)
    school_id: Mapped[int | None] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    school: Mapped["School | None"] = relationship(
        "School", back_populates="sync_provider"
    )

    def __repr__(self) -> str:
        return (
            f"<SyncProvider(code={self.code!r}, "
            f"active={self.is_active}, school_id={self.school_id})>"
        )
