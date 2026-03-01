"""Tests for BonusTask limit-based management and lifecycle."""

from datetime import datetime, timedelta, timezone

import pytest

from learning_hub.models.bonus_task import BonusTask
from learning_hub.models.enums import BonusTaskStatus
from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.models.subject_topic import SubjectTopic
from learning_hub.repositories.bonus_task import BonusTaskRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _create_topic(session) -> int:
    """Create school -> subject -> topic, return topic_id."""
    school = School(code="CZ", name="Czech School", is_active=True)
    session.add(school)
    await session.flush()

    subject = Subject(school_id=school.id, name="Math")
    session.add(subject)
    await session.flush()

    topic = SubjectTopic(subject_id=subject.id, description="Fractions")
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return topic.id


# Default limits for tests
MAX_PENDING = 4
MAX_COMPLETED = 15


# ---- create tests ----


async def test_create_within_limits(session):
    """Create succeeds when within both limits."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, limits = await repo.create(
        subject_topic_id=topic_id,
        task_description="Solve 5 fraction problems",
        max_pending=MAX_PENDING,
        max_completed_per_week=MAX_COMPLETED,
    )

    assert task is not None
    assert task.status == BonusTaskStatus.PENDING
    assert task.task_description == "Solve 5 fraction problems"
    assert limits["can_create"] is True


async def test_create_fails_pending_limit(session):
    """Create fails when pending count reaches the limit."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    # Fill up to the pending limit
    for i in range(MAX_PENDING):
        task, _ = await repo.create(
            topic_id, f"Task {i + 1}", MAX_PENDING, MAX_COMPLETED,
        )
        assert task is not None

    # Next one should fail
    task, limits = await repo.create(
        topic_id, "One too many", MAX_PENDING, MAX_COMPLETED,
    )

    assert task is None
    assert limits["can_create"] is False
    assert "pending" in limits["reason"].lower()


async def test_create_fails_weekly_limit(session):
    """Create fails when completed + pending reaches weekly limit."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    small_weekly_limit = 3

    # Complete 2 tasks
    for i in range(2):
        task, _ = await repo.create(
            topic_id, f"Task {i + 1}", MAX_PENDING, small_weekly_limit,
        )
        assert task is not None
        await repo.complete(task.id)

    # Create 1 pending (2 completed + 1 pending = 3 = limit)
    task, _ = await repo.create(
        topic_id, "Pending task", MAX_PENDING, small_weekly_limit,
    )
    assert task is not None

    # Next one should fail (2 completed + 1 pending >= 3)
    task, limits = await repo.create(
        topic_id, "Over limit", MAX_PENDING, small_weekly_limit,
    )

    assert task is None
    assert limits["can_create"] is False
    assert "weekly" in limits["reason"].lower()


async def test_cancel_stale_pending(session):
    """Stale pending tasks (>7 days old) are auto-cancelled on create."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    # Create a task and manually backdate it
    old_task = BonusTask(
        subject_topic_id=topic_id,
        task_description="Old stale task",
        status=BonusTaskStatus.PENDING,
    )
    session.add(old_task)
    await session.commit()
    await session.refresh(old_task)

    # Backdate created_at to 8 days ago
    old_task.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    await session.commit()

    # Creating a new task should auto-cancel the stale one
    new_task, limits = await repo.create(
        topic_id, "Fresh task", MAX_PENDING, MAX_COMPLETED,
    )

    assert new_task is not None
    await session.refresh(old_task)
    assert old_task.status == BonusTaskStatus.CANCELLED


# ---- complete tests ----


async def test_complete_task(session):
    """Completing a task sets status and completed_at."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, _ = await repo.create(
        topic_id, "Task to complete", MAX_PENDING, MAX_COMPLETED,
    )

    completed, error = await repo.complete(task.id, quality_notes="Well done")

    assert error is None
    assert completed.status == BonusTaskStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.quality_notes == "Well done"


async def test_complete_fails_for_completed_task(session):
    """Cannot complete an already-completed task."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, _ = await repo.create(
        topic_id, "Task", MAX_PENDING, MAX_COMPLETED,
    )
    await repo.complete(task.id)

    _, error = await repo.complete(task.id)
    assert error is not None
    assert "already" in error.lower()


async def test_complete_fails_for_cancelled_task(session):
    """Cannot complete a cancelled task."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, _ = await repo.create(
        topic_id, "Task", MAX_PENDING, MAX_COMPLETED,
    )
    await repo.cancel(task.id)

    _, error = await repo.complete(task.id)
    assert error is not None
    assert "already" in error.lower()


# ---- cancel tests ----


async def test_cancel_pending_task(session):
    """Cancelling a pending task sets status to CANCELLED."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, _ = await repo.create(
        topic_id, "Task to cancel", MAX_PENDING, MAX_COMPLETED,
    )
    cancelled, error = await repo.cancel(task.id)

    assert error is None
    assert cancelled.status == BonusTaskStatus.CANCELLED


async def test_cancel_fails_for_completed_task(session):
    """Cannot cancel an already-completed task."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, _ = await repo.create(
        topic_id, "Task", MAX_PENDING, MAX_COMPLETED,
    )
    await repo.complete(task.id)

    _, error = await repo.cancel(task.id)
    assert error is not None
    assert "already" in error.lower()


async def test_cancel_not_found(session):
    """Cancelling non-existent task returns error."""
    repo = BonusTaskRepository(session)
    _, error = await repo.cancel(999)
    assert error is not None
    assert "not found" in error.lower()


# ---- check_limits tests ----


async def test_check_limits_within_limits(session):
    """check_limits returns can_create=True when within limits."""
    repo = BonusTaskRepository(session)
    limits = await repo.check_limits(MAX_PENDING, MAX_COMPLETED)

    assert limits["can_create"] is True
    assert limits["pending_count"] == 0
    assert limits["completed_7d"] == 0
