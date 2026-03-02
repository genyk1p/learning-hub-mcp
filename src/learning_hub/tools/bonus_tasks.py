"""BonusTask tools for MCP server."""

import random
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import BonusTaskStatus, GradeValue, TopicReviewStatus
from learning_hub.models.enums import TransactionType
from learning_hub.models.subject_topic import SubjectTopic
from learning_hub.repositories.bonus_task import BonusTaskRepository
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.minute_transaction import MinuteTransactionRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.tools.config_vars import (
    CFG_GRADE_MINUTES_MAP,
    CFG_MAX_COMPLETED_BONUS_TASKS_PER_WEEK,
    CFG_MAX_PENDING_BONUS_TASKS,
)
from learning_hub.tools.tool_names import (
    TOOL_CREATE_BONUS_TASK,
    TOOL_LIST_BONUS_TASKS,
    TOOL_GET_BONUS_TASK,
    TOOL_GET_LATEST_BONUS_TASK,
    TOOL_CANCEL_BONUS_TASK,
    TOOL_APPLY_BONUS_TASK_RESULT,
    TOOL_CHECK_PENDING_BONUS_TASK,
    TOOL_CHECK_BONUS_AVAILABILITY,
    TOOL_CHECK_BONUS_LIMITS,
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


async def _read_limits(config_repo: ConfigEntryRepository) -> tuple[int, int]:
    """Read MAX_PENDING and MAX_COMPLETED_PER_WEEK from config."""
    max_pending_raw = await config_repo.get_value(CFG_MAX_PENDING_BONUS_TASKS)
    max_completed_raw = await config_repo.get_value(
        CFG_MAX_COMPLETED_BONUS_TASKS_PER_WEEK
    )
    max_pending = int(max_pending_raw) if max_pending_raw else 4
    max_completed = int(max_completed_raw) if max_completed_raw else 15
    return max_pending, max_completed


async def _check_limits(
    repo: BonusTaskRepository,
    max_pending: int,
    max_completed_per_week: int,
) -> dict:
    """Check if a new bonus task can be created within limits.

    Business logic: decides whether creation is allowed based on
    pending count and weekly completed count.
    """
    pending_count = await repo.count_pending()

    if pending_count >= max_pending:
        return {
            "pending_count": pending_count,
            "completed_7d": None,
            "can_create": False,
            "reason": (
                f"Too many pending tasks ({pending_count}/{max_pending}). "
                "Finish current tasks first."
            ),
        }

    since = datetime.now() - timedelta(days=7)
    completed_7d = await repo.count_completed_since(since)

    if completed_7d + pending_count >= max_completed_per_week:
        return {
            "pending_count": pending_count,
            "completed_7d": completed_7d,
            "can_create": False,
            "reason": (
                f"Weekly limit reached "
                f"({completed_7d} completed + {pending_count} pending "
                f">= {max_completed_per_week})."
            ),
        }

    return {
        "pending_count": pending_count,
        "completed_7d": completed_7d,
        "can_create": True,
        "reason": None,
    }


def register_bonus_task_tools(mcp: FastMCP) -> None:
    """Register bonus task-related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in BonusTaskStatus)

    @mcp.tool(name=TOOL_CREATE_BONUS_TASK, description="""Create a new bonus task.

    Bonus tasks are additional work that student can do to earn a grade.
    Tasks are linked to a subject topic.

    Validates that limits are not exceeded (max pending, max completed per week).

    Args:
        subject_topic_id: ID of the topic this task is related to
        task_description: Description of what student needs to do

    Returns:
        Created bonus task with limits info, or error message
    """)
    async def create_bonus_task(
        subject_topic_id: int,
        task_description: str,
    ) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            config_repo = ConfigEntryRepository(session)

            max_pending, max_completed = await _read_limits(config_repo)

            # Cancel stale pending tasks first
            await repo.cancel_stale_pending()

            # Check limits
            limits = await _check_limits(repo, max_pending, max_completed)
            if not limits["can_create"]:
                return {"error": limits["reason"], "limits": limits}

            task = await repo.create(
                subject_topic_id=subject_topic_id,
                task_description=task_description,
            )
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
                "limits": limits,
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
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            config_repo = ConfigEntryRepository(session)

            # Cancel stale pending tasks (older than 7 days) first
            cancelled = await repo.cancel_stale_pending()
            if cancelled:
                await session.commit()

            tasks = await repo.list(
                status=BonusTaskStatus.PENDING,
                limit=50,
                order_asc=False,
            )
            if not tasks:
                return None

            # If pending limit is reached, always return a task (no coin flip)
            max_pending, _ = await _read_limits(config_repo)
            if len(tasks) < max_pending:
                # Coin flip: 50% chance to create a new task instead
                if random.randint(0, 1) == 0:
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

    @mcp.tool(name=TOOL_CHECK_BONUS_AVAILABILITY, description="""Check how many bonus tasks the student can still complete this week.

    Returns:
        Availability: completed this week, remaining this week, and whether more can be done
    """)
    async def check_bonus_availability() -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            config_repo = ConfigEntryRepository(session)
            _, max_completed = await _read_limits(config_repo)
            since = datetime.now() - timedelta(days=7)
            completed_7d = await repo.count_completed_since(since)
            remaining = max(0, max_completed - completed_7d)
            return {
                "can_do_more": remaining > 0,
                "completed_this_week": completed_7d,
                "remaining_this_week": remaining,
            }

    @mcp.tool(name=TOOL_CHECK_BONUS_LIMITS, description="""Check if a new bonus task can be created (pending + weekly limits).

    Returns:
        can_create, pending_count, completed_7d, reason (if blocked)
    """)
    async def check_bonus_limits() -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusTaskRepository(session)
            config_repo = ConfigEntryRepository(session)
            max_pending, max_completed = await _read_limits(config_repo)
            return await _check_limits(repo, max_pending, max_completed)

    @mcp.tool(name=TOOL_APPLY_BONUS_TASK_RESULT, description="""Complete a bonus task, record the grade, and update topic reviews.

    This is a compound tool that does everything needed to finalize a bonus task:
    1. Marks the bonus task as completed
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
            tx_repo = MinuteTransactionRepository(session)
            config_repo = ConfigEntryRepository(session)

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
            task, error = await bonus_repo.complete(
                task_id=task_id,
                quality_notes=quality_notes,
            )
            if error is not None:
                return {"error": error}
            assert task is not None

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

            # Create BONUS_TASK transaction (grade_id intentionally not set
            # to avoid double-counting)
            grade_map_raw = await config_repo.get_json_value(CFG_GRADE_MINUTES_MAP)
            grade_minutes_map = (
                {int(k): v for k, v in grade_map_raw.items()}
                if isinstance(grade_map_raw, dict)
                else {1: 15, 2: 10, 3: 0, 4: -20, 5: -25}
            )
            tx_minutes = grade_minutes_map.get(grade_value, 0)
            if tx_minutes != 0:
                await tx_repo.create(
                    minutes=tx_minutes,
                    type=TransactionType.BONUS_TASK,
                    description=f"Bonus task: {task.task_description[:60]}",
                    bonus_task_id=task.id,
                )

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
                "grade": grade_result,
                "topic_reviews_updated": updated_reviews,
                "topic_reviews_reinforced": auto_reinforced,
            }
