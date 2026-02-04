"""Subject tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import SchoolType
from learning_hub.repositories.subject import SubjectRepository


class SubjectResponse(BaseModel):
    """Subject response schema."""
    id: int
    school: str
    name: str
    name_ru: str | None
    grade_level: int | None
    is_active: bool


def register_subject_tools(mcp: FastMCP) -> None:
    """Register subject-related tools."""

    school_options = ", ".join(f'"{s.value}"' for s in SchoolType)

    @mcp.tool(description=f"""Create a new school subject.

    Args:
        school: School type - one of: {school_options}
        name: Subject name in school's language
        name_ru: Subject name in Russian (optional)
        grade_level: Grade level 1-20 (optional)

    Returns:
        Created subject
    """)
    async def create_subject(
        school: str,
        name: str,
        name_ru: str | None = None,
        grade_level: int | None = None,
    ) -> SubjectResponse:
        school_enum = SchoolType(school)

        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subject = await repo.create(
                school=school_enum,
                name=name,
                name_ru=name_ru,
                grade_level=grade_level,
            )
            return SubjectResponse(
                id=subject.id,
                school=subject.school.value,
                name=subject.name,
                name_ru=subject.name_ru,
                grade_level=subject.grade_level,
                is_active=subject.is_active,
            )

    @mcp.tool(description=f"""List school subjects.

    Args:
        school: Filter by school type - one of: {school_options} (optional)
        is_active: Filter by active status (optional)

    Returns:
        List of subjects
    """)
    async def list_subjects(
        school: str | None = None,
        is_active: bool | None = None,
    ) -> list[SubjectResponse]:
        school_enum = SchoolType(school) if school else None

        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subjects = await repo.list(school=school_enum, is_active=is_active)
            return [
                SubjectResponse(
                    id=s.id,
                    school=s.school.value,
                    name=s.name,
                    name_ru=s.name_ru,
                    grade_level=s.grade_level,
                    is_active=s.is_active,
                )
                for s in subjects
            ]

    @mcp.tool(description="""Update a school subject.

    Args:
        subject_id: ID of the subject to update
        name: New subject name (optional)
        name_ru: New Russian name (optional)
        grade_level: New grade level (optional)
        is_active: Set active status (optional)

    Returns:
        Updated subject or null if not found
    """)
    async def update_subject(
        subject_id: int,
        name: str | None = None,
        name_ru: str | None = None,
        grade_level: int | None = None,
        is_active: bool | None = None,
    ) -> SubjectResponse | None:
        async with AsyncSessionLocal() as session:
            repo = SubjectRepository(session)
            subject = await repo.update(
                subject_id=subject_id,
                name=name,
                name_ru=name_ru,
                grade_level=grade_level,
                is_active=is_active,
            )
            if subject is None:
                return None
            return SubjectResponse(
                id=subject.id,
                school=subject.school.value,
                name=subject.name,
                name_ru=subject.name_ru,
                grade_level=subject.grade_level,
                is_active=subject.is_active,
            )
