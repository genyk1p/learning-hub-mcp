"""Escalation tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.grade import GradeRepository
from learning_hub.tools.tool_names import (
    TOOL_GET_GRADES_PENDING_ESCALATION,
    TOOL_MARK_GRADES_ESCALATED,
)
from learning_hub.utils import dt_to_str


class EscalationGradeResponse(BaseModel):
    """Grade with full context for escalation."""
    grade_id: int
    grade_value: int
    date: str | None
    subject_id: int
    subject_name: str
    subject_name_ru: str | None
    school: str
    subject_topic_id: int | None
    subject_topic_description: str | None
    escalated_at: str | None


class MarkEscalatedResponse(BaseModel):
    """Result of marking grades as escalated."""
    updated_count: int
    grade_ids: list[int]


def register_escalation_tools(mcp: FastMCP) -> None:
    """Register escalation-related tools."""

    @mcp.tool(name=TOOL_GET_GRADES_PENDING_ESCALATION, description="""Get grades that need escalation (notifying adult about bad grades).

    Returns grades where escalated_at is NULL and grade_value >= threshold.
    Each grade includes full context: subject name, school, topic description.

    Args:
        threshold: Grade value threshold (inclusive). Grades with this value
            and worse will be returned. One of: 2, 3, 4, 5
            (1=best, 5=worst). For example, threshold=3 returns grades 3, 4, 5.

    Returns:
        List of grades needing escalation with full subject/topic context
    """)
    async def get_grades_pending_escalation(
        threshold: int,
    ) -> list[EscalationGradeResponse]:
        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            grades = await repo.list_pending_escalation(threshold)
            return [
                EscalationGradeResponse(
                    grade_id=g.id,
                    grade_value=g.grade_value.value,
                    date=dt_to_str(g.date),
                    subject_id=g.subject_id,
                    subject_name=g.subject.name,
                    subject_name_ru=g.subject.name_ru,
                    school=g.subject.school.code,
                    subject_topic_id=g.subject_topic_id,
                    subject_topic_description=(
                        g.subject_topic.description if g.subject_topic else None
                    ),
                    escalated_at=dt_to_str(g.escalated_at),
                )
                for g in grades
            ]

    @mcp.tool(name=TOOL_MARK_GRADES_ESCALATED, description="""Mark grades as escalated (adult was notified).

    Sets escalated_at to current timestamp for the given grade IDs.
    Use this after notifying the adult about bad grades.

    Args:
        grade_ids: List of grade IDs to mark as escalated

    Returns:
        Count of updated grades and the IDs that were processed
    """)
    async def mark_grades_escalated(
        grade_ids: list[int],
    ) -> MarkEscalatedResponse:
        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            updated_count = await repo.mark_escalated(grade_ids)
            return MarkEscalatedResponse(
                updated_count=updated_count,
                grade_ids=grade_ids,
            )
