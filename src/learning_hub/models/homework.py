"""Homework model - homework assignments."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import HomeworkStatus, GradeValue

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.grade import Grade


class Homework(Base, TimestampMixin):
    """
    Homework assignment.

    Can have one grade when completed and graded.
    """

    __tablename__ = "homeworks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to subject (always required)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)

    # Foreign key to subject topic (optional)
    subject_topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("subject_topics.id"),
        nullable=True
    )

    # Description of homework or where to find it
    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Status
    status: Mapped[HomeworkStatus] = mapped_column(
        default=HomeworkStatus.PENDING,
        nullable=False
    )

    # When homework was assigned/received
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # When homework was completed
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Deadline for homework
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Whether penalty was applied for late/missing homework
    penalty_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Recommended grade from Emma (before teacher's final grade)
    recommended_grade: Mapped[GradeValue | None] = mapped_column(nullable=True)

    # External ID from EduPage (for sync deduplication)
    edupage_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="homeworks")
    subject_topic: Mapped["SubjectTopic | None"] = relationship("SubjectTopic", back_populates="homeworks")
    grade: Mapped["Grade | None"] = relationship("Grade", back_populates="homework")

    def __repr__(self) -> str:
        return (
            f"<Homework(id={self.id}, subject_id={self.subject_id}, "
            f"status={self.status.value})>"
        )
