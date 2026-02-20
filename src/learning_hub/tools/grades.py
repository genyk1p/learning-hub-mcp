"""Grade tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import GradeValue
from learning_hub.repositories.grade import GradeRepository
from learning_hub.tools.tool_names import (
    TOOL_ADD_GRADE,
    TOOL_LIST_GRADES,
    TOOL_UPDATE_GRADE,
)
from learning_hub.utils import dt_to_str


class GradeResponse(BaseModel):
    """Grade response schema."""
    id: int
    subject_id: int
    grade_value: int
    date: str | None
    subject_topic_id: int | None
    bonus_task_id: int | None
    homework_id: int | None
    rewarded: bool
    source: str


def register_grade_tools(mcp: FastMCP) -> None:
    """Register grade-related tools."""

    grade_value_options = ", ".join(str(g.value) for g in GradeValue)

    @mcp.tool(name=TOOL_ADD_GRADE, description=f"""Add a new grade.

    IMPORTANT: Uses 5-point European grading scale where 1 is BEST and 5 is WORST:
    - 1 = Excellent (A)
    - 2 = Good (B)
    - 3 = Satisfactory (C)
    - 4 = Poor (D)
    - 5 = Fail (F)

    If grade comes from a different system (US letters, 10-point, 100-point, etc.),
    YOU MUST convert it to this 1-5 scale before calling this tool.

    Args:
        subject_id: ID of the subject
        grade_value: Grade value - one of: {grade_value_options} (1=best, 5=worst)
        date: Grade date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        subject_topic_id: ID of the related topic (optional)
        bonus_task_id: ID of the related bonus task (optional)
        homework_id: ID of the related homework (optional)

    Returns:
        Created grade
    """)
    async def add_grade(
        subject_id: int,
        grade_value: int,
        date: str,
        subject_topic_id: int | None = None,
        bonus_task_id: int | None = None,
        homework_id: int | None = None,
    ) -> GradeResponse:
        grade_enum = GradeValue(grade_value)
        date_parsed = datetime.fromisoformat(date)

        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            grade = await repo.create(
                subject_id=subject_id,
                grade_value=grade_enum,
                date=date_parsed,
                subject_topic_id=subject_topic_id,
                bonus_task_id=bonus_task_id,
                homework_id=homework_id,
            )
            return GradeResponse(
                id=grade.id,
                subject_id=grade.subject_id,
                grade_value=grade.grade_value.value,
                date=dt_to_str(grade.date),
                subject_topic_id=grade.subject_topic_id,
                bonus_task_id=grade.bonus_task_id,
                homework_id=grade.homework_id,
                rewarded=grade.rewarded,
                source=grade.source.value,
            )

    @mcp.tool(name=TOOL_LIST_GRADES, description="""List grades with filters.

    Args:
        subject_id: Filter by subject ID (optional)
        school_id: Filter by school ID (optional)
        date_from: Filter grades from this date, ISO format (optional)
        date_to: Filter grades until this date, ISO format (optional)
        rewarded: Filter by rewarded status (optional)

    Returns:
        List of grades
    """)
    async def list_grades(
        subject_id: int | None = None,
        school_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        rewarded: bool | None = None,
    ) -> list[GradeResponse]:
        date_from_parsed = datetime.fromisoformat(date_from) if date_from else None
        date_to_parsed = datetime.fromisoformat(date_to) if date_to else None

        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            grades = await repo.list(
                subject_id=subject_id,
                school_id=school_id,
                date_from=date_from_parsed,
                date_to=date_to_parsed,
                rewarded=rewarded,
            )
            return [
                GradeResponse(
                    id=g.id,
                    subject_id=g.subject_id,
                    grade_value=g.grade_value.value,
                    date=dt_to_str(g.date),
                    subject_topic_id=g.subject_topic_id,
                    bonus_task_id=g.bonus_task_id,
                    homework_id=g.homework_id,
                    rewarded=g.rewarded,
                    source=g.source.value,
                )
                for g in grades
            ]

    @mcp.tool(name=TOOL_UPDATE_GRADE, description="""Update a grade.

    Args:
        grade_id: ID of the grade to update
        rewarded: Mark if grade was rewarded with game minutes (optional)

    Returns:
        Updated grade or null if not found
    """)
    async def update_grade(
        grade_id: int,
        rewarded: bool | None = None,
    ) -> GradeResponse | None:
        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            grade = await repo.update(
                grade_id=grade_id,
                rewarded=rewarded,
            )
            if grade is None:
                return None
            return GradeResponse(
                id=grade.id,
                subject_id=grade.subject_id,
                grade_value=grade.grade_value.value,
                date=dt_to_str(grade.date),
                subject_topic_id=grade.subject_topic_id,
                bonus_task_id=grade.bonus_task_id,
                homework_id=grade.homework_id,
                rewarded=grade.rewarded,
                source=grade.source.value,
            )
