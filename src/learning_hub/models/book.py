"""Book model - local library of educational materials."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from learning_hub.models.subject import Subject
    from learning_hub.models.homework import Homework


class Book(Base, TimestampMixin):
    """
    Book in the local library.

    Agent stores books in filesystem and saves references here.
    Books can optionally be linked to a school subject.
    """

    __tablename__ = "books"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Book title
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Original filename of the uploaded book file
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # Brief description of the book
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Path to the original book file (agent decides where to store it)
    original_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Path to the summary file (agent decides where to store it)
    summary_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Path to the contents index file (maps markdown chunks to topics/pages)
    contents_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Optional link to a school subject (SET NULL on subject delete)
    subject_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    subject: Mapped["Subject | None"] = relationship(
        "Subject", back_populates="books", foreign_keys=[subject_id]
    )
    homeworks: Mapped[list["Homework"]] = relationship("Homework", back_populates="book")

    def __repr__(self) -> str:
        subject_str = f", subject_id={self.subject_id}" if self.subject_id else ""
        return f"<Book(id={self.id}, title={self.title!r}{subject_str})>"
