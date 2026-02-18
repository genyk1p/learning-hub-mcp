"""Subject model - school subjects catalog."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.school import School
    from learning_hub.models.subject_topic import SubjectTopic
    from learning_hub.models.grade import Grade
    from learning_hub.models.homework import Homework
    from learning_hub.models.book import Book
    from learning_hub.models.family_member import FamilyMember


class Subject(Base, TimestampMixin):
    """
    School subject catalog.

    Each subject belongs to a specific school (UA or CZ).
    History in CZ school and History in UA school are different subjects.
    """

    __tablename__ = "subjects"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # School this subject belongs to
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
    )

    # Subject name in school's language
    # CZ: "Matematika", "Dějepis", "Zeměpis"
    # UA: "Математика", "Історія", "Географія"
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Russian name for display (optional)
    name_ru: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Grade level (class): 1-20, optional (e.g., "History 7th grade")
    grade_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Whether this subject is active (can deactivate old subjects)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Current textbook used for this subject (SET NULL on book delete)
    current_book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True
    )

    # Responsible tutor/adult for this subject (SET NULL on member delete)
    tutor_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="subjects")
    topics: Mapped[list["SubjectTopic"]] = relationship("SubjectTopic", back_populates="subject")
    grades: Mapped[list["Grade"]] = relationship("Grade", back_populates="subject")
    homeworks: Mapped[list["Homework"]] = relationship("Homework", back_populates="subject")
    books: Mapped[list["Book"]] = relationship(
        "Book", back_populates="subject", foreign_keys="Book.subject_id"
    )
    current_book: Mapped["Book | None"] = relationship("Book", foreign_keys=[current_book_id])
    tutor: Mapped["FamilyMember | None"] = relationship("FamilyMember", foreign_keys=[tutor_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "school_id", "name", "grade_level", name="uq_subject_school_name_grade"
        ),
        CheckConstraint(
            "grade_level IS NULL OR (grade_level >= 1 AND grade_level <= 20)",
            name="check_grade_level_range",
        ),
    )

    def __repr__(self) -> str:
        grade_str = f" grade {self.grade_level}" if self.grade_level else ""
        return f"<Subject(id={self.id}, school_id={self.school_id}, name={self.name!r}{grade_str})>"
