"""TopicReview model - topics that need reinforcement after bad grades."""

from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import TopicReviewStatus

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.grade import Grade


class TopicReview(Base, TimestampMixin):
    """
    Topic that needs reinforcement after receiving a grade > 1.

    Created automatically when syncing grades from EduPage.
    Only created if subject_topic_id exists for the grade.
    """

    __tablename__ = "topic_reviews"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to subject
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False
    )

    # Foreign key to subject topic
    subject_topic_id: Mapped[int] = mapped_column(
        ForeignKey("subject_topics.id"),
        nullable=False
    )

    # Foreign key to grade (unique - one review per grade)
    grade_id: Mapped[int] = mapped_column(
        ForeignKey("grades.id"),
        nullable=False,
        unique=True
    )

    # Review status
    status: Mapped[TopicReviewStatus] = mapped_column(
        default=TopicReviewStatus.PENDING,
        nullable=False
    )

    # How many times topic was repeated via bonus tasks
    repeat_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject")
    subject_topic: Mapped["SubjectTopic"] = relationship("SubjectTopic")
    grade: Mapped["Grade"] = relationship("Grade")

    def __repr__(self) -> str:
        return (
            f"<TopicReview(id={self.id}, topic_id={self.subject_topic_id}, "
            f"grade_id={self.grade_id}, status={self.status.value}, repeats={self.repeat_count})>"
        )
