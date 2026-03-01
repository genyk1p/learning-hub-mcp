"""Grade tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import GradeValue, TransactionType
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.minute_transaction import MinuteTransactionRepository
from learning_hub.tools.config_vars import CFG_GRADE_MINUTES_MAP
from learning_hub.tools.tool_names import (
    TOOL_ADD_GRADE,
    TOOL_LIST_GRADES,
)
from learning_hub.utils import dt_to_str

# Fallback if config DB is empty
_DEFAULT_GRADE_MINUTES_MAP = {1: 15, 2: 10, 3: 0, 4: -20, 5: -25}


class GradeResponse(BaseModel):
    """Grade response schema."""
    id: int
    subject_id: int
    grade_value: int
    original_value: str | None
    date: str | None
    subject_topic_id: int | None
    bonus_task_id: int | None
    homework_id: int | None
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

    A MinuteTransaction is automatically created for the grade (unless it is linked
    to a bonus_task_id — in that case apply_bonus_task_result handles the transaction).

    Args:
        subject_id: ID of the subject
        grade_value: Grade value - one of: {grade_value_options} (1=best, 5=worst)
        date: Grade date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        original_value: Original grade as entered by user or received from API
            (e.g. "1-", "2+", "A", "N"). Stored for display purposes. (optional)
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
        original_value: str | None = None,
        subject_topic_id: int | None = None,
        bonus_task_id: int | None = None,
        homework_id: int | None = None,
    ) -> GradeResponse | dict:
        grade_enum = GradeValue(grade_value)
        date_parsed = datetime.fromisoformat(date)

        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            try:
                grade = await repo.create(
                    subject_id=subject_id,
                    grade_value=grade_enum,
                    date=date_parsed,
                    subject_topic_id=subject_topic_id,
                    bonus_task_id=bonus_task_id,
                    homework_id=homework_id,
                    original_value=original_value,
                )
            except ValueError as e:
                return {"error": str(e)}

            # Create GRADE transaction unless this grade belongs to a bonus task
            # (bonus tasks create their own BONUS_TASK transaction in apply_bonus_task_result)
            if grade.bonus_task_id is None:
                config_repo = ConfigEntryRepository(session)
                grade_map_raw = await config_repo.get_json_value(CFG_GRADE_MINUTES_MAP)
                grade_minutes_map = (
                    {int(k): v for k, v in grade_map_raw.items()}
                    if isinstance(grade_map_raw, dict)
                    else _DEFAULT_GRADE_MINUTES_MAP
                )
                minutes = grade_minutes_map.get(grade_value, 0)
                if minutes != 0:
                    tx_repo = MinuteTransactionRepository(session)
                    await tx_repo.create(
                        minutes=minutes,
                        type=TransactionType.GRADE,
                        description=f"Grade {grade_value}",
                        grade_id=grade.id,
                    )

            return GradeResponse(
                id=grade.id,
                subject_id=grade.subject_id,
                grade_value=grade.grade_value.value,
                original_value=grade.original_value,
                date=dt_to_str(grade.date),
                subject_topic_id=grade.subject_topic_id,
                bonus_task_id=grade.bonus_task_id,
                homework_id=grade.homework_id,
                source=grade.source,
            )

    @mcp.tool(name=TOOL_LIST_GRADES, description="""List grades with filters.

    Args:
        subject_id: Filter by subject ID (optional)
        school_id: Filter by school ID (optional)
        date_from: Filter grades from this date, ISO format (optional)
        date_to: Filter grades until this date, ISO format (optional)

    Returns:
        List of grades
    """)
    async def list_grades(
        subject_id: int | None = None,
        school_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
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
            )
            return [
                GradeResponse(
                    id=g.id,
                    subject_id=g.subject_id,
                    grade_value=g.grade_value.value,
                    original_value=g.original_value,
                    date=dt_to_str(g.date),
                    subject_topic_id=g.subject_topic_id,
                    bonus_task_id=g.bonus_task_id,
                    homework_id=g.homework_id,
                    source=g.source,
                )
                for g in grades
            ]
