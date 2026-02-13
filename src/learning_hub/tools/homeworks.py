"""Homework tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import HomeworkStatus, GradeValue
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.utils import dt_to_str


class HomeworkResponse(BaseModel):
    """Homework response schema."""
    id: int
    subject_id: int
    subject_topic_id: int | None
    book_id: int | None
    description: str
    status: str
    assigned_at: str | None
    deadline_at: str | None
    completed_at: str | None
    penalty_applied: bool
    recommended_grade: int | None


def register_homework_tools(mcp: FastMCP) -> None:
    """Register homework-related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in HomeworkStatus)
    grade_options = ", ".join(str(g.value) for g in GradeValue)

    @mcp.tool(description="""Create a new homework assignment.

    Args:
        subject_id: ID of the subject
        description: Homework description
        subject_topic_id: ID of the related topic (optional)
        book_id: ID of the related book (optional)
        assigned_at: When homework was assigned, ISO format (optional, defaults to now)
        deadline_at: Deadline for homework, ISO format (optional)

    Returns:
        Created homework
    """)
    async def create_homework(
        subject_id: int,
        description: str,
        subject_topic_id: int | None = None,
        book_id: int | None = None,
        assigned_at: str | None = None,
        deadline_at: str | None = None,
    ) -> HomeworkResponse:
        assigned_parsed = datetime.fromisoformat(assigned_at) if assigned_at else None
        deadline_parsed = datetime.fromisoformat(deadline_at) if deadline_at else None

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            hw = await repo.create(
                subject_id=subject_id,
                description=description,
                subject_topic_id=subject_topic_id,
                book_id=book_id,
                assigned_at=assigned_parsed,
                deadline_at=deadline_parsed,
            )
            return HomeworkResponse(
                id=hw.id,
                subject_id=hw.subject_id,
                subject_topic_id=hw.subject_topic_id,
                book_id=hw.book_id,
                description=hw.description,
                status=hw.status.value,
                assigned_at=dt_to_str(hw.assigned_at),
                deadline_at=dt_to_str(hw.deadline_at),
                completed_at=None,
                penalty_applied=hw.penalty_applied,
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )

    @mcp.tool(description=f"""List homeworks.

    Args:
        subject_id: Filter by subject ID (optional)
        status: Filter by status - one of: {status_options} (optional)

    Returns:
        List of homeworks
    """)
    async def list_homeworks(
        subject_id: int | None = None,
        status: str | None = None,
    ) -> list[HomeworkResponse]:
        status_enum = HomeworkStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            homeworks = await repo.list(subject_id=subject_id, status=status_enum)
            return [
                HomeworkResponse(
                    id=hw.id,
                    subject_id=hw.subject_id,
                    subject_topic_id=hw.subject_topic_id,
                    book_id=hw.book_id,
                    description=hw.description,
                    status=hw.status.value,
                    assigned_at=dt_to_str(hw.assigned_at),
                    deadline_at=dt_to_str(hw.deadline_at),
                    completed_at=dt_to_str(hw.completed_at),
                    penalty_applied=hw.penalty_applied,
                    recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
                )
                for hw in homeworks
            ]

    @mcp.tool(description="""Mark homework as completed.

    Args:
        homework_id: ID of the homework to complete

    Returns:
        Completed homework or null if not found
    """)
    async def complete_homework(homework_id: int) -> HomeworkResponse | None:
        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            hw = await repo.complete(homework_id=homework_id)
            if hw is None:
                return None
            return HomeworkResponse(
                id=hw.id,
                subject_id=hw.subject_id,
                subject_topic_id=hw.subject_topic_id,
                book_id=hw.book_id,
                description=hw.description,
                status=hw.status.value,
                assigned_at=dt_to_str(hw.assigned_at),
                deadline_at=dt_to_str(hw.deadline_at),
                completed_at=dt_to_str(hw.completed_at),
                penalty_applied=hw.penalty_applied,
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )

    @mcp.tool(description=f"""Update homework.

    Args:
        homework_id: ID of the homework to update
        description: New description (optional)
        deadline_at: New deadline, ISO format (optional)
        recommended_grade: Expected grade - one of: {grade_options} (1=best, 5=worst) (optional)
        penalty_applied: Mark if penalty was applied for late submission (optional)
        status: New status - one of: {status_options} (optional)
        book_id: ID of the related book (optional)
        clear_book: Set to true to remove book link (optional)

    Returns:
        Updated homework or null if not found
    """)
    async def update_homework(
        homework_id: int,
        description: str | None = None,
        deadline_at: str | None = None,
        recommended_grade: int | None = None,
        penalty_applied: bool | None = None,
        status: str | None = None,
        book_id: int | None = None,
        clear_book: bool = False,
    ) -> HomeworkResponse | None:
        deadline_parsed = datetime.fromisoformat(deadline_at) if deadline_at else None
        grade_enum = GradeValue(recommended_grade) if recommended_grade else None
        status_enum = HomeworkStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            hw = await repo.update(
                homework_id=homework_id,
                description=description,
                deadline_at=deadline_parsed,
                recommended_grade=grade_enum,
                penalty_applied=penalty_applied,
                status=status_enum,
                book_id=book_id,
                clear_book=clear_book,
            )
            if hw is None:
                return None
            return HomeworkResponse(
                id=hw.id,
                subject_id=hw.subject_id,
                subject_topic_id=hw.subject_topic_id,
                book_id=hw.book_id,
                description=hw.description,
                status=hw.status.value,
                assigned_at=dt_to_str(hw.assigned_at),
                deadline_at=dt_to_str(hw.deadline_at),
                completed_at=dt_to_str(hw.completed_at),
                penalty_applied=hw.penalty_applied,
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )
