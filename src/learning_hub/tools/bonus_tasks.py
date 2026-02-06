"""BonusTask tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import BonusTaskStatus, TopicReviewStatus
from learning_hub.repositories.bonus_task import BonusTaskRepository
from learning_hub.repositories.topic_review import TopicReviewRepository


class BonusTaskResponse(BaseModel):
    """BonusTask response schema."""
    id: int
    subject_topic_id: int
    fund_id: int
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
    Tasks are linked to a subject topic and a bonus fund.

    Validates that the fund has enough minutes for the promised reward.
    Minutes are NOT deducted at creation - only when task is completed.

    Args:
        subject_topic_id: ID of the topic this task is related to
        task_description: Description of what student needs to do
        minutes_promised: Number of game minutes promised for completing this task
        fund_id: ID of the bonus fund that will pay for this task

    Returns:
        Created bonus task with fund info, or error message
    """)
    async def create_bonus_task(
        subject_topic_id: int,
        task_description: str,
        minutes_promised: int,
        fund_id: int,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task, fund, error = await repo.create(
                subject_topic_id=subject_topic_id,
                task_description=task_description,
                minutes_promised=minutes_promised,
                fund_id=fund_id,
            )
            if error is not None:
                return {"error": error, "fund_minutes_available": fund.minutes if fund else None}
            assert task is not None
            assert fund is not None
            return {
                "task": BonusTaskResponse(
                    id=task.id,
                    subject_topic_id=task.subject_topic_id,
                    fund_id=task.fund_id,
                    task_description=task.task_description,
                    minutes_promised=task.minutes_promised,
                    status=task.status.value,
                    created_at=task.created_at,
                    completed_at=None,
                    quality_notes=None,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_minutes_available": fund.minutes,
            }

    @mcp.tool(description=f"""List bonus tasks.

    Args:
        subject_topic_id: Filter by topic ID (optional)
        status: Filter by status - one of: {status_options} (optional)
        created_from: Filter by created_at >= this datetime, ISO format (optional)
        created_to: Filter by created_at < this datetime, ISO format (optional)
        limit: Max number of results, 1-200 (optional, default 50)
        order: Sort order - one of: "created_at_asc", "created_at_desc" (optional, default "created_at_desc")

    Returns:
        List of bonus tasks
    """)
    async def list_bonus_tasks(
        subject_topic_id: int | None = None,
        status: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[BonusTaskResponse]:
        status_enum = BonusTaskStatus(status) if status else None
        parsed_from = datetime.fromisoformat(created_from) if created_from else None
        parsed_to = datetime.fromisoformat(created_to) if created_to else None
        clamped_limit = min(max(limit, 1), 200) if limit is not None else 50
        order_asc = order == "created_at_asc"

        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            tasks = await repo.list(
                subject_topic_id=subject_topic_id,
                status=status_enum,
                created_from=parsed_from,
                created_to=parsed_to,
                limit=clamped_limit,
                order_asc=order_asc,
            )
            return [
                BonusTaskResponse(
                    id=t.id,
                    subject_topic_id=t.subject_topic_id,
                    fund_id=t.fund_id,
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

    Automatically deducts the promised minutes from the bonus fund linked to the task.

    Args:
        task_id: ID of the bonus task to complete
        quality_notes: Optional notes about quality of work done

    Returns:
        Completed task with fund info, or error message
    """)
    async def complete_bonus_task(
        task_id: int,
        quality_notes: str | None = None,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task, fund, error = await repo.complete(
                task_id=task_id,
                quality_notes=quality_notes,
            )
            if error is not None:
                return {"error": error}
            assert task is not None
            assert fund is not None
            return {
                "task": BonusTaskResponse(
                    id=task.id,
                    subject_topic_id=task.subject_topic_id,
                    fund_id=task.fund_id,
                    task_description=task.task_description,
                    minutes_promised=task.minutes_promised,
                    status=task.status.value,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                    quality_notes=task.quality_notes,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_minutes_remaining": fund.minutes,
                "minutes_deducted": task.minutes_promised,
            }

    @mcp.tool(description="""Get a bonus task by ID.

    Args:
        task_id: ID of the bonus task

    Returns:
        Bonus task or null if not found
    """)
    async def get_bonus_task(task_id: int) -> BonusTaskResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task = await repo.get_by_id(task_id)
            if task is None:
                return None
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                fund_id=task.fund_id,
                task_description=task.task_description,
                minutes_promised=task.minutes_promised,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=task.completed_at,
                quality_notes=task.quality_notes,
            )

    @mcp.tool(description=f"""Get the most recent bonus task matching filters.

    Useful for quickly finding the latest task without listing all.

    Args:
        status: Filter by status - one of: {status_options} (optional)
        subject_topic_id: Filter by topic ID (optional)

    Returns:
        Latest matching bonus task or null if none found
    """)
    async def get_latest_bonus_task(
        status: str | None = None,
        subject_topic_id: int | None = None,
    ) -> BonusTaskResponse | None:
        status_enum = BonusTaskStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            tasks = await repo.list(
                status=status_enum,
                subject_topic_id=subject_topic_id,
                limit=1,
                order_asc=False,
            )
            if not tasks:
                return None
            task = tasks[0]
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                fund_id=task.fund_id,
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
                fund_id=task.fund_id,
                task_description=task.task_description,
                minutes_promised=task.minutes_promised,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=task.completed_at,
                quality_notes=task.quality_notes,
            )

    @mcp.tool(description="""Complete a bonus task and optionally update related topic reviews.

    1. Marks the bonus task as completed (deducts minutes from fund)
    2. If count_repeat is true: finds all pending TopicReviews for the same subject topic
       and increments repeat_count on each

    Args:
        task_id: ID of the bonus task to complete
        count_repeat: Whether to increment repeat_count on pending topic reviews (default true)
        quality_notes: Optional notes about quality of work done

    Returns:
        Completed task info + list of updated topic reviews
    """)
    async def apply_bonus_task_result(
        task_id: int,
        count_repeat: bool = True,
        quality_notes: str | None = None,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            bonus_repo = BonusTaskRepository(session)
            review_repo = TopicReviewRepository(session)

            task, fund, error = await bonus_repo.complete(
                task_id=task_id,
                quality_notes=quality_notes,
            )
            if error is not None:
                return {"error": error}
            assert task is not None
            assert fund is not None

            # Find and increment pending reviews for the same topic
            updated_reviews = []
            if count_repeat:
                pending_reviews = await review_repo.list(
                    subject_topic_id=task.subject_topic_id,
                    status=TopicReviewStatus.PENDING,
                )
                for review in pending_reviews:
                    updated = await review_repo.increment_repeat_count(review.id)
                    if updated is not None:
                        updated_reviews.append({
                            "review_id": updated.id,
                            "repeat_count": updated.repeat_count,
                            "topic_description": updated.subject_topic.description,
                        })

            return {
                "task": BonusTaskResponse(
                    id=task.id,
                    subject_topic_id=task.subject_topic_id,
                    fund_id=task.fund_id,
                    task_description=task.task_description,
                    minutes_promised=task.minutes_promised,
                    status=task.status.value,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                    quality_notes=task.quality_notes,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_minutes_remaining": fund.minutes,
                "minutes_deducted": task.minutes_promised,
                "topic_reviews_updated": updated_reviews,
            }
