"""Bonus model - bonus minutes linked to homework or ad-hoc."""

from typing import TYPE_CHECKING
from sqlalchemy import Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.homework import Homework


class Bonus(Base, TimestampMixin):
    """
    Bonus minutes record.

    Records how many bonus minutes were awarded (or deducted).
    Minutes can be positive (reward) or negative (penalty).

    Two modes:
    - Homework-linked: homework_id set, one bonus per homework (unique constraint).
    - Ad-hoc: homework_id is NULL, reason describes why (e.g. "good behavior").
    """

    __tablename__ = "bonuses"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to homework (optional, unique - one bonus per homework)
    homework_id: Mapped[int | None] = mapped_column(
        ForeignKey("homeworks.id"),
        nullable=True,
        unique=True,
    )

    # Bonus minutes (positive = reward, negative = penalty)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional reason for ad-hoc bonuses (when no homework_id)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether these minutes were counted in weekly calculation
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    homework: Mapped["Homework | None"] = relationship("Homework", back_populates="bonus")

    def __repr__(self) -> str:
        return (
            f"<Bonus(id={self.id}, homework_id={self.homework_id}, "
            f"minutes={self.minutes}, reason={self.reason!r}, rewarded={self.rewarded})>"
        )
