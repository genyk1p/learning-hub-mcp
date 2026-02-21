"""Week model - weekly calculation of game minutes."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from learning_hub.models.base import Base, TimestampMixin


class Week(Base, TimestampMixin):
    """
    Weekly calculation of game minutes.

    Aggregates grades, bonuses, penalties for a week period (Saturday to Saturday).
    No foreign keys - just a snapshot of calculated values.
    """

    __tablename__ = "weeks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Week identifier (Saturday date, e.g. "2026-02-01")
    week_key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    # Period start (Saturday morning after calculation)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Period end (next Saturday morning)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Minutes from grades (1→+15, 2→+10, 3→0, 4→-20, 5→-25)
    grade_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Sum of all bonuses for this week: homework bonuses (+/- per homework)
    # AND ad-hoc bonuses (parent rewards/penalties without homework link)
    homework_bonus_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Penalty minutes (for late topics, missed deadlines, etc.)
    penalty_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Carryover out: remaining minutes after finalization (can be positive or negative)
    carryover_out_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # How many minutes actually played
    actual_played_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Total balance (grade - penalty + carryover - played)
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Whether this week is finalized (closed for changes)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        status = "finalized" if self.is_finalized else "open"
        return f"<Week(key={self.week_key}, total={self.total_minutes}, status={status})>"
