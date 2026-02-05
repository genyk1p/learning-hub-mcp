"""SubjectTopic model - topics within a subject."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import CloseReason

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.bonus_task import BonusTask
    from learning_hub.models.grade import Grade
    from learning_hub.models.homework import Homework


class SubjectTopic(Base, TimestampMixin):
    """
    Topic within a subject.

    Can be closed when resolved, skipped, or no longer relevant.
    """

    __tablename__ = "subject_topics"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to subject this topic belongs to
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)

    # Description of the topic
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # When topic was closed (null = still active)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Reason why topic was closed
    close_reason: Mapped[CloseReason | None] = mapped_column(nullable=True)

    # Relationship to Subject
    subject: Mapped["Subject"] = relationship("Subject", back_populates="topics")

    # Relationship to BonusTasks
    bonus_tasks: Mapped[list["BonusTask"]] = relationship("BonusTask", back_populates="subject_topic")

    # Relationship to Grades
    grades: Mapped[list["Grade"]] = relationship("Grade", back_populates="subject_topic")

    # Relationship to Homeworks
    homeworks: Mapped[list["Homework"]] = relationship("Homework", back_populates="subject_topic")

    # Unique constraint to prevent duplicate topics per subject
    __table_args__ = (
        UniqueConstraint("subject_id", "description", name="uq_subject_topic_subject_description"),
    )

    def __repr__(self) -> str:
        if self.closed_at is None:
            status = "active"
        else:
            reason = self.close_reason.value if self.close_reason else "unknown"
            status = f"closed ({reason})"
        return f"<SubjectTopic(id={self.id}, subject_id={self.subject_id}, status={status})>"
