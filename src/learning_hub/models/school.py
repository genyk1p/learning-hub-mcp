"""School model - school/education system catalog."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject


class School(Base, TimestampMixin):
    """
    School / education system.

    Each school represents a country-level education system (CZ, UA, etc.)
    with its own grading scale description.
    """

    __tablename__ = "schools"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ISO 3166-1 alpha-2 country code (e.g. "CZ", "UA")
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)

    # Human-readable school name
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Free-text description of the grading system for the AI agent
    grading_system: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether this school is currently active
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    subjects: Mapped[list["Subject"]] = relationship("Subject", back_populates="school")

    def __repr__(self) -> str:
        return f"<School(id={self.id}, code={self.code!r}, name={self.name!r})>"
