"""BonusTask tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import BonusTaskStatus
from learning_hub.repositories.bonus_task import BonusTaskRepository


class BonusTaskResponse(BaseModel):
    """BonusTask response schema."""
    id: int
    subject_topic_id: int
    task_description: str
    minutes_promised: int
    status: str
    created_at: datetime | None
    completed_at: datetime | None
    quality_notes: str | None


def register_bonus_task_tools(mcp: FastMCP) -> None:
    """Register bonus task-related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in BonusTaskStatus)

    @mcp.tool(description="""Create a new bonus task.

    Bonus tasks are additional work that student can do to earn game minutes.
    Tasks are linked to a subject topic.

    Args:
        subject_topic_id: ID of the topic this task is related to
        task_description: Description of what student needs to do
        minutes_promised: Number of game minutes promised for completing this task

    Returns:
        Created bonus task
    """)
    async def create_bonus_task(
        subject_topic_id: int,
        task_description: str,
        minutes_promised: int,
    ) -> BonusTaskResponse:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task = await repo.create(
                subject_topic_id=subject_topic_id,
                task_description=task_description,
                minutes_promised=minutes_promised,
            )
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                task_description=task.task_description,
                minutes_promised=task.minutes_promised,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=None,
                quality_notes=None,
            )

    @mcp.tool(description=f"""List bonus tasks.

    Args:
        subject_topic_id: Filter by topic ID (optional)
        status: Filter by status - one of: {status_options} (optional)

    Returns:
        List of bonus tasks
    """)
    async def list_bonus_tasks(
        subject_topic_id: int | None = None,
        status: str | None = None,
    ) -> list[BonusTaskResponse]:
        status_enum = BonusTaskStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            tasks = await repo.list(
                subject_topic_id=subject_topic_id,
                status=status_enum,
            )
            return [
                BonusTaskResponse(
                    id=t.id,
                    subject_topic_id=t.subject_topic_id,
                    task_description=t.task_description,
                    minutes_promised=t.minutes_promised,
                    status=t.status.value,
                    created_at=t.created_at,
                    completed_at=t.completed_at,
                    quality_notes=t.quality_notes,
                )
                for t in tasks
            ]

    @mcp.tool(description="""Mark a bonus task as completed.

    Args:
        task_id: ID of the bonus task to complete
        quality_notes: Optional notes about quality of work done

    Returns:
        Completed task or null if not found
    """)
    async def complete_bonus_task(
        task_id: int,
        quality_notes: str | None = None,
    ) -> BonusTaskResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task = await repo.complete(task_id=task_id, quality_notes=quality_notes)
            if task is None:
                return None
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                task_description=task.task_description,
                minutes_promised=task.minutes_promised,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=task.completed_at,
                quality_notes=task.quality_notes,
            )

    @mcp.tool(description="""Cancel a bonus task.

    Use this when a promised task is no longer relevant or was cancelled.

    Args:
        task_id: ID of the bonus task to cancel

    Returns:
        Cancelled task or null if not found
    """)
    async def cancel_bonus_task(task_id: int) -> BonusTaskResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task = await repo.cancel(task_id=task_id)
            if task is None:
                return None
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                task_description=task.task_description,
                minutes_promised=task.minutes_promised,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=task.completed_at,
                quality_notes=task.quality_notes,
            )
