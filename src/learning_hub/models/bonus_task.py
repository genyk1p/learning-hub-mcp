"""BonusTask model - bonus tasks for students to earn extra game minutes."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import BonusTaskStatus

if TYPE_CHECKING:
    from learning_hub.models.bonus_fund import BonusFund
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.grade import Grade


class BonusTask(Base, TimestampMixin):
    """
    Bonus task that student can complete to earn extra game minutes.

    Lifecycle:
    1. PENDING - task created, waiting for completion
    2. COMPLETED - student completed the task
    3. CANCELLED - task was cancelled
    """

    __tablename__ = "bonus_tasks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to subject topic this task is for
    subject_topic_id: Mapped[int] = mapped_column(
        ForeignKey("subject_topics.id"),
        nullable=False
    )

    # Foreign key to bonus fund (singleton, always id=1)
    fund_id: Mapped[int] = mapped_column(
        ForeignKey("bonus_funds.id"),
        nullable=False
    )

    # Description of the task
    task_description: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Current status of the task
    status: Mapped[BonusTaskStatus] = mapped_column(
        default=BonusTaskStatus.PENDING,
        nullable=False
    )

    # When student completed the task
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Notes about quality of completion
    quality_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship to BonusFund
    fund: Mapped["BonusFund"] = relationship("BonusFund")

    # Relationship to SubjectTopic
    subject_topic: Mapped["SubjectTopic"] = relationship("SubjectTopic", back_populates="bonus_tasks")

    # Relationship to Grade (one bonus task can have one grade)
    grade: Mapped["Grade | None"] = relationship("Grade", back_populates="bonus_task")

    def __repr__(self) -> str:
        return (
            f"<BonusTask(id={self.id}, topic_id={self.subject_topic_id}, "
            f"status={self.status.value})>"
        )
