"""Homework tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import HomeworkStatus, GradeValue
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.tools.config_vars import (
    CFG_HOMEWORK_BONUS_MINUTES_ONTIME,
    CFG_HOMEWORK_BONUS_MINUTES_OVERDUE,
)
from learning_hub.tools.tool_names import (
    TOOL_CREATE_HOMEWORK,
    TOOL_LIST_HOMEWORKS,
    TOOL_CLOSE_OVERDUE_HOMEWORKS,
    TOOL_COMPLETE_HOMEWORK,
    TOOL_UPDATE_HOMEWORK,
    TOOL_GET_PENDING_HOMEWORK_REMINDERS,
    TOOL_MARK_HOMEWORK_REMINDERS_SENT,
)
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
    recommended_grade: int | None


class HomeworkReminderResponse(BaseModel):
    """A homework reminder to be sent (D-1 or D-2)."""
    homework_id: int
    subject_name: str
    subject_name_ru: str | None
    description: str
    deadline_at: str
    kind: str  # "d1" or "d2"


class MarkRemindedResponse(BaseModel):
    """Result of marking homework reminders as sent."""
    updated_count: int
    d1_homework_ids: list[int]
    d2_homework_ids: list[int]


def register_homework_tools(mcp: FastMCP) -> None:
    """Register homework-related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in HomeworkStatus)
    grade_options = ", ".join(str(g.value) for g in GradeValue)

    @mcp.tool(name=TOOL_CREATE_HOMEWORK, description="""Create a new homework assignment.

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
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )

    @mcp.tool(name=TOOL_LIST_HOMEWORKS, description=f"""List homeworks.

    Args:
        subject_id: Filter by subject ID (optional)
        status: Filter by status - one of: {status_options} (optional)
        limit: Max number of results, 1-200 (optional, default 20)

    Returns:
        List of homeworks
    """)
    async def list_homeworks(
        subject_id: int | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[HomeworkResponse]:
        status_enum = HomeworkStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            homeworks = await repo.list(subject_id=subject_id, status=status_enum, limit=limit)
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
                    recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
                )
                for hw in homeworks
            ]

    @mcp.tool(name=TOOL_CLOSE_OVERDUE_HOMEWORKS, description=f"""Close all overdue homeworks.

    Finds all pending homeworks where deadline has passed and marks them
    as overdue with a penalty from {CFG_HOMEWORK_BONUS_MINUTES_OVERDUE} config.
    Homeworks without a deadline are not affected.

    Returns:
        List of closed homeworks
    """)
    async def close_overdue_homeworks() -> list[HomeworkResponse]:
        async with AsyncSessionLocal() as session:
            config_repo = ConfigEntryRepository(session)
            ontime = await config_repo.get_int_value(CFG_HOMEWORK_BONUS_MINUTES_ONTIME) or 5
            overdue = await config_repo.get_int_value(CFG_HOMEWORK_BONUS_MINUTES_OVERDUE) or -5

            repo = HomeworkRepository(session)
            closed = await repo.close_overdue(
                ontime_bonus=ontime,
                overdue_penalty=overdue,
            )
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
                    recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
                )
                for hw in closed
            ]

    @mcp.tool(name=TOOL_COMPLETE_HOMEWORK, description=f"""Mark homework as completed.

    Optionally sets recommended_grade in the same call (so you don't need
    a separate update_homework call before completing).

    Args:
        homework_id: ID of the homework to complete
        recommended_grade: Expected grade - one of: {grade_options} (1=best, 5=worst) (optional)

    Returns:
        Completed homework or null if not found
    """)
    async def complete_homework(
        homework_id: int,
        recommended_grade: int | None = None,
    ) -> HomeworkResponse | dict | None:
        if recommended_grade is not None and recommended_grade >= 4:
            return {
                "error": (
                    f"Cannot complete homework with grade {recommended_grade}. "
                    "Grades 4-5 mean the student should redo the work."
                ),
            }

        grade_enum = GradeValue(recommended_grade) if recommended_grade else None

        async with AsyncSessionLocal() as session:
            config_repo = ConfigEntryRepository(session)
            ontime = await config_repo.get_int_value(CFG_HOMEWORK_BONUS_MINUTES_ONTIME) or 5
            overdue_pen = await config_repo.get_int_value(CFG_HOMEWORK_BONUS_MINUTES_OVERDUE) or -5

            repo = HomeworkRepository(session)
            hw = await repo.complete(
                homework_id=homework_id,
                ontime_bonus=ontime,
                overdue_penalty=overdue_pen,
                recommended_grade=grade_enum,
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
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )

    @mcp.tool(name=TOOL_UPDATE_HOMEWORK, description=f"""Update homework.

    To change homework status use complete_homework instead.

    Args:
        homework_id: ID of the homework to update
        description: New description (optional)
        deadline_at: New deadline, ISO format (optional)
        recommended_grade: Expected grade - one of: {grade_options} (1=best, 5=worst) (optional)
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
        book_id: int | None = None,
        clear_book: bool = False,
    ) -> HomeworkResponse | None:
        deadline_parsed = datetime.fromisoformat(deadline_at) if deadline_at else None
        grade_enum = GradeValue(recommended_grade) if recommended_grade else None

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            hw = await repo.update(
                homework_id=homework_id,
                description=description,
                deadline_at=deadline_parsed,
                recommended_grade=grade_enum,
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
                recommended_grade=hw.recommended_grade.value if hw.recommended_grade else None,
            )

    @mcp.tool(name=TOOL_GET_PENDING_HOMEWORK_REMINDERS, description="""Get homework reminders that should be sent now.

    Returns pending homeworks approaching their deadline that haven't been reminded yet:
    - D-2: deadline is in 2 days (not yet reminded for D-2)
    - D-1: deadline is tomorrow (not yet reminded for D-1)

    Dedup is built-in: each homework appears at most once per kind.

    Returns:
        List of reminders with subject context, or empty list
    """)
    async def get_pending_homework_reminders() -> list[HomeworkReminderResponse]:
        today = datetime.now().date()

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            homeworks = await repo.list_pending_with_deadline()

            reminders: list[HomeworkReminderResponse] = []
            for hw in homeworks:
                dl = hw.deadline_at
                # Handle legacy timezone-aware datetimes (convert to local)
                if dl.tzinfo is not None:
                    dl = dl.astimezone()
                deadline_date = dl.date()
                days_until = (deadline_date - today).days

                if days_until == 2 and hw.reminded_d2_at is None:
                    kind = "d2"
                elif days_until == 1 and hw.reminded_d1_at is None:
                    kind = "d1"
                else:
                    continue

                reminders.append(HomeworkReminderResponse(
                    homework_id=hw.id,
                    subject_name=hw.subject.name,
                    subject_name_ru=hw.subject.name_ru,
                    description=hw.description,
                    deadline_at=dt_to_str(hw.deadline_at),
                    kind=kind,
                ))

            return reminders

    @mcp.tool(name=TOOL_MARK_HOMEWORK_REMINDERS_SENT, description="""Mark homework reminders as sent.

    Sets reminded_d1_at / reminded_d2_at timestamps for the given homework IDs.
    Call this after successfully delivering the reminders.

    Args:
        d1_homework_ids: Homework IDs that received D-1 reminder (optional)
        d2_homework_ids: Homework IDs that received D-2 reminder (optional)

    Returns:
        Count of updated records and the IDs that were processed
    """)
    async def mark_homework_reminders_sent(
        d1_homework_ids: list[int] | None = None,
        d2_homework_ids: list[int] | None = None,
    ) -> MarkRemindedResponse:
        d1_ids = d1_homework_ids or []
        d2_ids = d2_homework_ids or []

        async with AsyncSessionLocal() as session:
            repo = HomeworkRepository(session)
            updated = await repo.mark_reminded(d1_ids, d2_ids)
            return MarkRemindedResponse(
                updated_count=updated,
                d1_homework_ids=d1_ids,
                d2_homework_ids=d2_ids,
            )
