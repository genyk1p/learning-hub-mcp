"""MinuteTransaction model - ledger of earned and spent game minutes."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class MinuteTransaction(Base, TimestampMixin):
    """
    Ledger entry for game minutes.

    Each event (grade, homework, bonus task, played time) creates one record.
    Current balance = SUM(minutes) across all records.
    """

    __tablename__ = "minute_transactions"
    __table_args__ = (
        UniqueConstraint("homework_id", name="uq_minute_transactions_homework_id"),
        UniqueConstraint("bonus_task_id", name="uq_minute_transactions_bonus_task_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Positive = earned, negative = spent or penalty
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Transaction type (TransactionType enum value stored as string)
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Human-readable description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source — at most one is set
    grade_id: Mapped[int | None] = mapped_column(
        ForeignKey("grades.id"), nullable=True
    )
    homework_id: Mapped[int | None] = mapped_column(
        ForeignKey("homeworks.id"), nullable=True
    )
    bonus_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("bonus_tasks.id"), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<MinuteTransaction(id={self.id}, minutes={self.minutes:+d}, "
            f"type={self.type!r})>"
        )
