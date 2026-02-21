"""BonusTask tools for MCP server."""

import random
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import BonusTaskStatus, GradeValue, TopicReviewStatus
from learning_hub.models.subject_topic import SubjectTopic
from learning_hub.repositories.bonus_task import BonusTaskRepository
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_BONUS_TASK,
    TOOL_LIST_BONUS_TASKS,
    TOOL_COMPLETE_BONUS_TASK,
    TOOL_GET_BONUS_TASK,
    TOOL_GET_LATEST_BONUS_TASK,
    TOOL_CANCEL_BONUS_TASK,
    TOOL_APPLY_BONUS_TASK_RESULT,
    TOOL_CHECK_PENDING_BONUS_TASK,
)
from learning_hub.utils import dt_to_str


class BonusTaskResponse(BaseModel):
    """BonusTask response schema."""
    id: int
    subject_topic_id: int
    task_description: str
    status: str
    created_at: str | None
    completed_at: str | None
    quality_notes: str | None


def register_bonus_task_tools(mcp: FastMCP) -> None:
    """Register bonus task-related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in BonusTaskStatus)

    @mcp.tool(name=TOOL_CREATE_BONUS_TASK, description="""Create a new bonus task.

    Bonus tasks are additional work that student can do to earn a grade.
    Tasks are linked to a subject topic. A slot is deducted from the bonus fund.

    Validates that the bonus fund has available task slots.

    Args:
        subject_topic_id: ID of the topic this task is related to
        task_description: Description of what student needs to do

    Returns:
        Created bonus task with fund info, or error message
    """)
    async def create_bonus_task(
        subject_topic_id: int,
        task_description: str,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task, fund, error = await repo.create(
                subject_topic_id=subject_topic_id,
                task_description=task_description,
            )
            if error is not None:
                return {"error": error, "available_tasks": fund.available_tasks if fund else None}
            assert task is not None
            assert fund is not None
            return {
                "task": BonusTaskResponse(
                    id=task.id,
                    subject_topic_id=task.subject_topic_id,
                    task_description=task.task_description,
                    status=task.status.value,
                    created_at=dt_to_str(task.created_at),
                    completed_at=None,
                    quality_notes=None,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_available_tasks": fund.available_tasks,
            }

    @mcp.tool(name=TOOL_LIST_BONUS_TASKS, description=f"""List bonus tasks.

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
                    task_description=t.task_description,
                    status=t.status.value,
                    created_at=dt_to_str(t.created_at),
                    completed_at=dt_to_str(t.completed_at),
                    quality_notes=t.quality_notes,
                )
                for t in tasks
            ]

    @mcp.tool(name=TOOL_COMPLETE_BONUS_TASK, description="""Mark a bonus task as completed.

    Deducts one task slot from the bonus fund.

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
                    task_description=task.task_description,
                    status=task.status.value,
                    created_at=dt_to_str(task.created_at),
                    completed_at=dt_to_str(task.completed_at),
                    quality_notes=task.quality_notes,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_available_tasks": fund.available_tasks,
            }

    @mcp.tool(name=TOOL_GET_BONUS_TASK, description="""Get a bonus task by ID.

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
                task_description=task.task_description,
                status=task.status.value,
                created_at=dt_to_str(task.created_at),
                completed_at=dt_to_str(task.completed_at),
                quality_notes=task.quality_notes,
            )

    @mcp.tool(name=TOOL_GET_LATEST_BONUS_TASK, description=f"""Get the most recent bonus task matching filters.

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
                task_description=task.task_description,
                status=task.status.value,
                created_at=dt_to_str(task.created_at),
                completed_at=dt_to_str(task.completed_at),
                quality_notes=task.quality_notes,
            )

    @mcp.tool(name=TOOL_CANCEL_BONUS_TASK, description="""Cancel a bonus task.

    Use this when a pending task is no longer relevant or was cancelled.

    Args:
        task_id: ID of the bonus task to cancel

    Returns:
        Cancelled task data, or error dict if not found or not in pending status
    """)
    async def cancel_bonus_task(task_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            task, error = await repo.cancel(task_id=task_id)
            if task is None:
                return {"error": error or "Task not found"}
            if error is not None:
                return {
                    "error": error,
                    "task": BonusTaskResponse(
                        id=task.id,
                        subject_topic_id=task.subject_topic_id,
                        task_description=task.task_description,
                        status=task.status.value,
                        created_at=dt_to_str(task.created_at),
                        completed_at=dt_to_str(task.completed_at),
                        quality_notes=task.quality_notes,
                    ).model_dump(),
                }
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                task_description=task.task_description,
                status=task.status.value,
                created_at=dt_to_str(task.created_at),
                completed_at=dt_to_str(task.completed_at),
                quality_notes=task.quality_notes,
            ).model_dump()

    @mcp.tool(name=TOOL_CHECK_PENDING_BONUS_TASK, description="""Check if there's a pending bonus task to reuse.

    Flips a coin: 50% chance returns a random pending bonus task,
    50% chance returns null (so a new task gets created instead).
    This prevents the student from always getting the same old task
    while still recycling unfinished ones.

    Returns:
        A pending bonus task to reuse, or null if none picked
    """)
    async def check_pending_bonus_task() -> BonusTaskResponse | None:
        if random.randint(0, 1) == 0:
            return None

        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            tasks = await repo.list(
                status=BonusTaskStatus.PENDING,
                limit=50,
                order_asc=False,
            )
            if not tasks:
                return None
            task = random.choice(tasks)
            return BonusTaskResponse(
                id=task.id,
                subject_topic_id=task.subject_topic_id,
                task_description=task.task_description,
                status=task.status.value,
                created_at=dt_to_str(task.created_at),
                completed_at=dt_to_str(task.completed_at),
                quality_notes=task.quality_notes,
            )

    @mcp.tool(name=TOOL_APPLY_BONUS_TASK_RESULT, description="""Complete a bonus task, record the grade, and update topic reviews.

    This is a compound tool that does everything needed to finalize a bonus task:
    1. Marks the bonus task as completed (deducts one slot from fund)
    2. Creates a grade linked to this bonus task
       (subject_id is resolved automatically from the task's topic)
    3. If count_repeat is true: finds all pending TopicReviews for the same subject topic,
       increments repeat_count on each, and auto-closes reviews that reached
       the repetition threshold (from TOPIC_REVIEW_THRESHOLDS config)

    Args:
        task_id: ID of the bonus task to complete
        grade_value: Grade for the bonus task (1-5, European scale: 1=best, 5=worst)
        count_repeat: Whether to increment repeat_count on pending topic reviews (default true)
        quality_notes: Optional notes about quality of work done

    Returns:
        Completed task info + grade info + list of updated/auto-reinforced topic reviews
    """)
    async def apply_bonus_task_result(
        task_id: int,
        grade_value: int,
        count_repeat: bool = True,
        quality_notes: str | None = None,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            bonus_repo = BonusTaskRepository(session)
            review_repo = TopicReviewRepository(session)
            grade_repo = GradeRepository(session)

            # --- Pre-validate everything BEFORE any mutations ---
            try:
                grade_enum = GradeValue(grade_value)
            except ValueError:
                return {"error": f"Invalid grade_value={grade_value}. Must be 1-5."}

            if grade_enum.value >= 4:
                return {
                    "error": (
                        f"Cannot close bonus task with grade {grade_value}. "
                        "Grades 4-5 mean the student should retry."
                    ),
                }

            pre_task = await bonus_repo.get_by_id(task_id)
            if pre_task is None:
                return {"error": f"Task {task_id} not found"}

            topic = await session.get(SubjectTopic, pre_task.subject_topic_id)
            if topic is None:
                return {
                    "error": f"SubjectTopic {pre_task.subject_topic_id} not found",
                }

            # --- All validated, now mutate ---
            task, fund, error = await bonus_repo.complete(
                task_id=task_id,
                quality_notes=quality_notes,
            )
            if error is not None:
                return {"error": error}
            assert task is not None
            assert fund is not None

            # Create grade linked to this bonus task
            try:
                grade = await grade_repo.create(
                    subject_id=topic.subject_id,
                    grade_value=grade_enum,
                    date=datetime.now(),
                    subject_topic_id=task.subject_topic_id,
                    bonus_task_id=task.id,
                )
            except ValueError as e:
                return {"error": str(e)}

            grade_result = {
                "grade_id": grade.id,
                "grade_value": grade.grade_value.value,
                "original_value": grade.original_value,
                "subject_id": grade.subject_id,
            }

            updated_reviews = []
            auto_reinforced = []

            if count_repeat:
                # Read thresholds config for auto-close
                config_repo = ConfigEntryRepository(session)
                thresholds = await config_repo.get_json_value(
                    "TOPIC_REVIEW_THRESHOLDS",
                ) or {}

                pending_reviews = await review_repo.list(
                    subject_topic_id=task.subject_topic_id,
                    status=TopicReviewStatus.PENDING,
                )
                for review in pending_reviews:
                    updated = await review_repo.increment_repeat_count(review.id)
                    if updated is None:
                        continue

                    updated_reviews.append({
                        "review_id": updated.id,
                        "repeat_count": updated.repeat_count,
                        "topic_description": updated.subject_topic.description,
                    })

                    # Auto-close if threshold reached
                    grade_val = str(updated.grade.grade_value.value)
                    required = thresholds.get(grade_val)
                    if required is not None and updated.repeat_count >= required:
                        reinforced = await review_repo.mark_reinforced(updated.id)
                        if reinforced is None:
                            continue
                        auto_reinforced.append({
                            "review_id": updated.id,
                            "topic_description": updated.subject_topic.description,
                            "grade_value": updated.grade.grade_value.value,
                            "repeat_count": updated.repeat_count,
                            "threshold": required,
                        })

            return {
                "task": BonusTaskResponse(
                    id=task.id,
                    subject_topic_id=task.subject_topic_id,
                    task_description=task.task_description,
                    status=task.status.value,
                    created_at=dt_to_str(task.created_at),
                    completed_at=dt_to_str(task.completed_at),
                    quality_notes=task.quality_notes,
                ).model_dump(),
                "fund_name": fund.name,
                "fund_available_tasks": fund.available_tasks,
                "grade": grade_result,
                "topic_reviews_updated": updated_reviews,
                "topic_reviews_reinforced": auto_reinforced,
            }
