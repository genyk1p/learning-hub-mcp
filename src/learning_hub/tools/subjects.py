"""Subject tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_SUBJECT,
    TOOL_LIST_SUBJECTS,
    TOOL_UPDATE_SUBJECT,
)


class SubjectResponse(BaseModel):
    """Subject response schema."""
    id: int
    school_id: int
    name: str
    name_ru: str | None
    grade_level: int | None
    is_active: bool
    current_book_id: int | None
    tutor_id: int | None


def register_subject_tools(mcp: FastMCP) -> None:
    """Register subject-related tools."""

    @mcp.tool(name=TOOL_CREATE_SUBJECT, description="""Create a new school subject.

    Args:
        school_id: ID of the school this subject belongs to (from list_schools)
        name: Subject name in school's language
        name_ru: Subject name in Russian (optional)
        grade_level: Grade level 1-20 (optional)

    Returns:
        Created subject
    """)
    async def create_subject(
        school_id: int,
        name: str,
        name_ru: str | None = None,
        grade_level: int | None = None,
    ) -> SubjectResponse:
        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subject = await repo.create(
                school_id=school_id,
                name=name,
                name_ru=name_ru,
                grade_level=grade_level,
            )
            return SubjectResponse(
                id=subject.id,
                school_id=subject.school_id,
                name=subject.name,
                name_ru=subject.name_ru,
                grade_level=subject.grade_level,
                is_active=subject.is_active,
                current_book_id=subject.current_book_id,
                tutor_id=subject.tutor_id,
            )

    @mcp.tool(name=TOOL_LIST_SUBJECTS, description="""List school subjects.

    Args:
        school_id: Filter by school ID (optional)
        is_active: Filter by active status (optional)

    Returns:
        List of subjects
    """)
    async def list_subjects(
        school_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[SubjectResponse]:
        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subjects = await repo.list(school_id=school_id, is_active=is_active)
            return [
                SubjectResponse(
                    id=s.id,
                    school_id=s.school_id,
                    name=s.name,
                    name_ru=s.name_ru,
                    grade_level=s.grade_level,
                    is_active=s.is_active,
                    current_book_id=s.current_book_id,
                    tutor_id=s.tutor_id,
                )
                for s in subjects
            ]

    @mcp.tool(name=TOOL_UPDATE_SUBJECT, description="""Update a school subject.

    Args:
        subject_id: ID of the subject to update
        name: New subject name (optional)
        name_ru: New Russian name (optional)
        grade_level: New grade level (optional)
        is_active: Set active status (optional)
        current_book_id: ID of the current textbook for this subject (optional)
        clear_current_book: Set to true to remove current textbook link (optional)
        tutor_id: ID of the responsible tutor/adult for this subject (optional)
        clear_tutor: Set to true to remove tutor link (optional)

    Returns:
        Updated subject or null if not found
    """)
    async def update_subject(
        subject_id: int,
        name: str | None = None,
        name_ru: str | None = None,
        grade_level: int | None = None,
        is_active: bool | None = None,
        current_book_id: int | None = None,
        clear_current_book: bool = False,
        tutor_id: int | None = None,
        clear_tutor: bool = False,
    ) -> SubjectResponse | None:
        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subject = await repo.update(
                subject_id=subject_id,
                name=name,
                name_ru=name_ru,
                grade_level=grade_level,
                is_active=is_active,
                current_book_id=current_book_id,
                clear_current_book=clear_current_book,
                tutor_id=tutor_id,
                clear_tutor=clear_tutor,
            )
            if subject is None:
                return None
            return SubjectResponse(
                id=subject.id,
                school_id=subject.school_id,
                name=subject.name,
                name_ru=subject.name_ru,
                grade_level=subject.grade_level,
                is_active=subject.is_active,
                current_book_id=subject.current_book_id,
                tutor_id=subject.tutor_id,
            )
