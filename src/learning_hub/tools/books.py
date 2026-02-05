"""Book tools for MCP server."""

from datetime import datetime
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.book import BookRepository


class BookResponse(BaseModel):
    """Book response schema."""
    id: int
    title: str
    description: str | None
    original_path: str | None
    summary_path: str | None
    subject_id: int | None
    created_at: datetime
    updated_at: datetime


def register_book_tools(mcp: FastMCP) -> None:
    """Register book-related tools."""

    @mcp.tool(description="""Add a new book to the library.

    Args:
        title: Book title
        description: Brief description of the book (optional)
        original_path: Path to the original book file (optional)
        summary_path: Path to the summary file (optional)
        subject_id: ID of the related subject (optional)

    Returns:
        Created book
    """)
    async def add_book(
        title: str,
        description: str | None = None,
        original_path: str | None = None,
        summary_path: str | None = None,
        subject_id: int | None = None,
    ) -> BookResponse:
        async with AsyncSessionLocal() as session:
            repo = BookRepository(session)
            book = await repo.create(
                title=title,
                description=description,
                original_path=original_path,
                summary_path=summary_path,
                subject_id=subject_id,
            )
            return BookResponse(
                id=book.id,
                title=book.title,
                description=book.description,
                original_path=book.original_path,
                summary_path=book.summary_path,
                subject_id=book.subject_id,
                created_at=book.created_at,
                updated_at=book.updated_at,
            )

    @mcp.tool(description="""List books from the library.

    Args:
        subject_id: Filter by subject ID (optional)
        has_summary: Filter by presence of summary - true/false (optional)

    Returns:
        List of books
    """)
    async def list_books(
        subject_id: int | None = None,
        has_summary: bool | None = None,
    ) -> list[BookResponse]:
        async with AsyncSessionLocal() as session:
            repo = BookRepository(session)
            books = await repo.list(subject_id=subject_id, has_summary=has_summary)
            return [
                BookResponse(
                    id=b.id,
                    title=b.title,
                    description=b.description,
                    original_path=b.original_path,
                    summary_path=b.summary_path,
                    subject_id=b.subject_id,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                )
                for b in books
            ]

    @mcp.tool(description="""Get a book by ID.

    Args:
        book_id: ID of the book

    Returns:
        Book or null if not found
    """)
    async def get_book(book_id: int) -> BookResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BookRepository(session)
            book = await repo.get_by_id(book_id)
            if book is None:
                return None
            return BookResponse(
                id=book.id,
                title=book.title,
                description=book.description,
                original_path=book.original_path,
                summary_path=book.summary_path,
                subject_id=book.subject_id,
                created_at=book.created_at,
                updated_at=book.updated_at,
            )

    @mcp.tool(description="""Update a book.

    Args:
        book_id: ID of the book to update
        title: New title (optional)
        description: New description (optional)
        original_path: New original file path (optional)
        summary_path: New summary file path (optional)
        subject_id: New subject ID (optional)
        clear_subject: Set to true to remove subject link (optional)

    Returns:
        Updated book or null if not found
    """)
    async def update_book(
        book_id: int,
        title: str | None = None,
        description: str | None = None,
        original_path: str | None = None,
        summary_path: str | None = None,
        subject_id: int | None = None,
        clear_subject: bool = False,
    ) -> BookResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BookRepository(session)
            book = await repo.update(
                book_id=book_id,
                title=title,
                description=description,
                original_path=original_path,
                summary_path=summary_path,
                subject_id=subject_id,
                clear_subject=clear_subject,
            )
            if book is None:
                return None
            return BookResponse(
                id=book.id,
                title=book.title,
                description=book.description,
                original_path=book.original_path,
                summary_path=book.summary_path,
                subject_id=book.subject_id,
                created_at=book.created_at,
                updated_at=book.updated_at,
            )

    @mcp.tool(description="""Delete a book from the library.

    Args:
        book_id: ID of the book to delete

    Returns:
        True if deleted, False if not found
    """)
    async def delete_book(book_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            repo = BookRepository(session)
            return await repo.delete(book_id)
