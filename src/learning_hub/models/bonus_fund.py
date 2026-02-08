"""BonusFund model - pool of available bonus tasks."""

from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class BonusFund(Base, TimestampMixin):
    """
    Bonus fund - a quota of bonus tasks that can be assigned.

    Singleton: only one row with id=1 is allowed.
    Agent manages available task slots.
    Slots are deducted when bonus tasks are created.
    """

    __tablename__ = "bonus_funds"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_bonus_funds_singleton"),
    )

    # Primary key (always 1)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

    # Fund name (agent creates a creative name)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # How many bonus tasks can be assigned from this fund
    available_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<BonusFund(id={self.id}, name={self.name!r}, available_tasks={self.available_tasks})>"
