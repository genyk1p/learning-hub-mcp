"""Repository for Book model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.book import Book


class BookRepository:
    """Repository for Book CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        title: str,
        original_filename: str,
        description: str | None = None,
        original_path: str | None = None,
        summary_path: str | None = None,
        contents_path: str | None = None,
        subject_id: int | None = None,
    ) -> Book:
        """Create a new book."""
        book = Book(
            title=title,
            original_filename=original_filename,
            description=description,
            original_path=original_path,
            summary_path=summary_path,
            contents_path=contents_path,
            subject_id=subject_id,
        )
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def get_by_id(self, book_id: int) -> Book | None:
        """Get book by ID."""
        return await self.session.get(Book, book_id)

    async def list(
        self,
        subject_id: int | None = None,
        has_summary: bool | None = None,
    ) -> list[Book]:
        """List books with optional filters."""
        query = select(Book)

        if subject_id is not None:
            query = query.where(Book.subject_id == subject_id)

        if has_summary is True:
            query = query.where(Book.summary_path.isnot(None))
        elif has_summary is False:
            query = query.where(Book.summary_path.is_(None))

        query = query.order_by(Book.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        book_id: int,
        title: str | None = None,
        original_filename: str | None = None,
        description: str | None = None,
        original_path: str | None = None,
        summary_path: str | None = None,
        contents_path: str | None = None,
        subject_id: int | None = None,
        clear_subject: bool = False,
    ) -> Book | None:
        """Update book fields. Returns None if not found.

        Args:
            book_id: ID of the book to update
            title: New title (optional)
            original_filename: New original filename (optional)
            description: New description (optional)
            original_path: New original path (optional)
            summary_path: New summary path (optional)
            contents_path: New contents index path (optional)
            subject_id: New subject ID (optional)
            clear_subject: If True, sets subject_id to None (optional)
        """
        book = await self.get_by_id(book_id)
        if book is None:
            return None

        if title is not None:
            book.title = title
        if original_filename is not None:
            book.original_filename = original_filename
        if description is not None:
            book.description = description
        if original_path is not None:
            book.original_path = original_path
        if summary_path is not None:
            book.summary_path = summary_path
        if contents_path is not None:
            book.contents_path = contents_path
        if clear_subject:
            book.subject_id = None
        elif subject_id is not None:
            book.subject_id = subject_id

        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: int) -> bool:
        """Delete book by ID. Returns True if deleted, False if not found."""
        book = await self.get_by_id(book_id)
        if book is None:
            return False

        await self.session.delete(book)
        await self.session.commit()
        return True
