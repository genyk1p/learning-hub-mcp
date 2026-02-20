"""Grade model - student grades from schools."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import GradeSource, GradeValue

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.bonus_task import BonusTask
    from learning_hub.models.homework import Homework


class Grade(Base, TimestampMixin):
    """
    Student grade from school.

    Grade scale: 1 (best) to 5 (worst)
    School is determined by the linked Subject.

    Can be linked to:
    - Subject only (grade without known topic)
    - SubjectTopic (grade for specific topic)
    - BonusTask (grade for completing bonus task)
    - Homework (grade for homework)
    """

    __tablename__ = "grades"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to subject (always required)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)

    # Foreign key to subject topic (optional - if topic is known)
    subject_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("subject_topics.id"),
        nullable=True
    )

    # Foreign key to bonus task (optional - if grade is for bonus task)
    bonus_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("bonus_tasks.id"),
        nullable=True
    )

    # Foreign key to homework (optional - if grade is for homework)
    homework_id: Mapped[int | None] = mapped_column(
        ForeignKey("homeworks.id"),
        nullable=True
    )

    # Grade value: 1-5 (1 is best, 5 is worst) (auto-validated by Enum)
    grade_value: Mapped[GradeValue] = mapped_column(nullable=False)

    # Date when grade was received (stored in UTC, displayed in Europe/Vienna)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Whether bonuses/penalties for this grade were counted in weekly calculation
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Date when escalation was performed (notifying adult about bad grade)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # How this grade was entered: auto (EduPage sync, etc.) or manual (human/agent)
    source: Mapped[GradeSource] = mapped_column(
        String(10), default=GradeSource.MANUAL, nullable=False
    )

    # External ID from EduPage (for sync deduplication)
    edupage_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="grades")
    subject_topic: Mapped["SubjectTopic | None"] = relationship("SubjectTopic", back_populates="grades")
    bonus_task: Mapped["BonusTask | None"] = relationship("BonusTask", back_populates="grade")
    homework: Mapped["Homework | None"] = relationship("Homework", back_populates="grade")

    def __repr__(self) -> str:
        return (
            f"<Grade(id={self.id}, subject_id={self.subject_id}, "
            f"grade={self.grade_value.value}, date={self.date.date()})>"
        )
