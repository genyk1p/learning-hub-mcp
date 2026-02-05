"""BonusFund model - pool of bonus minutes for rewards."""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class BonusFund(Base, TimestampMixin):
    """
    Bonus fund - a pool of minutes that can be awarded for extra tasks.

    Agent creates funds with creative names and manages available minutes.
    Minutes are deducted when awarded for bonus tasks.
    """

    __tablename__ = "bonus_funds"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Fund name (agent creates a creative name)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Available minutes in the fund
    minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<BonusFund(id={self.id}, name={self.name!r}, minutes={self.minutes})>"
