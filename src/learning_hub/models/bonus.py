"""Bonus model - bonus minutes that can be linked to homework or other entities."""

from typing import TYPE_CHECKING
from sqlalchemy import Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.homework import Homework


class Bonus(Base, TimestampMixin):
    """
    Bonus minutes record.

    Records how many bonus minutes were awarded (or deducted) for a homework.
    Minutes can be positive (reward) or negative (penalty).
    Each homework can have at most one bonus record.
    """

    __tablename__ = "bonuses"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to homework (required, unique - one bonus per homework)
    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id"),
        nullable=False,
        unique=True
    )

    # Bonus minutes (positive = reward, negative = penalty)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Whether these minutes were counted in weekly calculation
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    homework: Mapped["Homework"] = relationship("Homework", back_populates="bonus")

    def __repr__(self) -> str:
        return (
            f"<Bonus(id={self.id}, homework_id={self.homework_id}, "
            f"minutes={self.minutes}, rewarded={self.rewarded})>"
        )
