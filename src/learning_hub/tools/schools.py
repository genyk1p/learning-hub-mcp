"""School tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.school import SchoolRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_SCHOOL,
    TOOL_GET_SCHOOL,
    TOOL_LIST_SCHOOLS,
    TOOL_UPDATE_SCHOOL,
)


class SchoolResponse(BaseModel):
    """School response schema."""
    id: int
    code: str
    name: str
    grading_system: str | None
    is_active: bool


def register_school_tools(mcp: FastMCP) -> None:
    """Register school-related tools."""

    @mcp.tool(name=TOOL_CREATE_SCHOOL, description="""Create a new school (education system).

    Args:
        code: ISO 3166-1 alpha-2 country code (e.g. "CZ", "UA", "DE")
        name: Human-readable school name (e.g. "Česká škola")
        grading_system: Free-text description of the grading system for AI agent (optional)

    Returns:
        Created school
    """)
    async def create_school(
        code: str,
        name: str,
        grading_system: str | None = None,
    ) -> SchoolResponse:
        async with AsyncSessionLocal() as session:
            repo = SchoolRepository(session)
            school = await repo.create(
                code=code,
                name=name,
                grading_system=grading_system,
            )
            return SchoolResponse(
                id=school.id,
                code=school.code,
                name=school.name,
                grading_system=school.grading_system,
                is_active=school.is_active,
            )

    @mcp.tool(name=TOOL_LIST_SCHOOLS, description="""List all schools (education systems).

    Args:
        is_active: Filter by active status (optional)

    Returns:
        List of schools
    """)
    async def list_schools(
        is_active: bool | None = None,
    ) -> list[SchoolResponse]:
        async with AsyncSessionLocal() as session:
            repo = SchoolRepository(session)
            schools = await repo.list(is_active=is_active)
            return [
                SchoolResponse(
                    id=s.id,
                    code=s.code,
                    name=s.name,
                    grading_system=s.grading_system,
                    is_active=s.is_active,
                )
                for s in schools
            ]

    @mcp.tool(name=TOOL_GET_SCHOOL, description="""Get a school by ID.

    Args:
        school_id: ID of the school

    Returns:
        School or null if not found
    """)
    async def get_school(school_id: int) -> SchoolResponse | None:
        async with AsyncSessionLocal() as session:
            repo = SchoolRepository(session)
            school = await repo.get_by_id(school_id)
            if school is None:
                return None
            return SchoolResponse(
                id=school.id,
                code=school.code,
                name=school.name,
                grading_system=school.grading_system,
                is_active=school.is_active,
            )

    @mcp.tool(name=TOOL_UPDATE_SCHOOL, description="""Update a school.

    Args:
        school_id: ID of the school to update
        name: New human-readable name (optional)
        grading_system: New grading system description (optional)
        is_active: Set active status (optional)
        clear_grading_system: Set to true to remove grading system description (optional)

    Returns:
        Updated school or null if not found
    """)
    async def update_school(
        school_id: int,
        name: str | None = None,
        grading_system: str | None = None,
        is_active: bool | None = None,
        clear_grading_system: bool = False,
    ) -> SchoolResponse | None:
        async with AsyncSessionLocal() as session:
            repo = SchoolRepository(session)
            school = await repo.update(
                school_id=school_id,
                name=name,
                grading_system=grading_system,
                is_active=is_active,
                clear_grading_system=clear_grading_system,
            )
            if school is None:
                return None
            return SchoolResponse(
                id=school.id,
                code=school.code,
                name=school.name,
                grading_system=school.grading_system,
                is_active=school.is_active,
            )
