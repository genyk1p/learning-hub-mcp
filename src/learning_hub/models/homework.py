"""Homework model - homework assignments."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import HomeworkStatus, GradeValue

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.grade import Grade
    from learning_hub.models.book import Book


class Homework(Base, TimestampMixin):
    """
    Homework assignment.

    Can have one grade when completed and graded.
    """

    __tablename__ = "homeworks"
    __table_args__ = (
        UniqueConstraint("external_id", "external_source", name="uq_homeworks_external"),
    )

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

    # Recommended grade from AI agent (before teacher's final grade)
    recommended_grade: Mapped[GradeValue | None] = mapped_column(nullable=True)

    # Optional link to a book
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True
    )

    # External ID for sync deduplication (provider-agnostic)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_source: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # URL from homework attachment (link type only, not files)
    attachment_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Reminder dedup: when D-2 / D-1 reminders were sent
    reminded_d2_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminded_d1_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="homeworks")
    subject_topic: Mapped["SubjectTopic | None"] = relationship("SubjectTopic", back_populates="homeworks")
    book: Mapped["Book | None"] = relationship("Book", back_populates="homeworks")
    grade: Mapped["Grade | None"] = relationship("Grade", back_populates="homework")

    def __repr__(self) -> str:
        return (
            f"<Homework(id={self.id}, subject_id={self.subject_id}, "
            f"status={self.status.value})>"
        )
