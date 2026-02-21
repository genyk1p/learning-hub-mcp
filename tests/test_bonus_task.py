"""Tests for BonusTask fund slot management and lifecycle."""

import pytest

from learning_hub.models.bonus_fund import BonusFund
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


async def _create_fund(session, available_tasks: int = 5) -> BonusFund:
    fund = BonusFund(id=1, name="Test Fund", available_tasks=available_tasks)
    session.add(fund)
    await session.commit()
    await session.refresh(fund)
    return fund


# ---- create tests ----


async def test_create_with_available_slots(session):
    """Create succeeds when fund has enough slots."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, fund, error = await repo.create(
        subject_topic_id=topic_id,
        task_description="Solve 5 fraction problems",
    )

    assert error is None
    assert task is not None
    assert task.status == BonusTaskStatus.PENDING
    assert task.task_description == "Solve 5 fraction problems"
    # Fund NOT deducted on create — only on complete
    assert fund.available_tasks == 5


async def test_create_auto_cancels_oldest_pending(session):
    """When fund at capacity, creating new task auto-cancels the oldest pending."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=2)
    repo = BonusTaskRepository(session)

    # Create 2 tasks — fills capacity (fund=2, pending=2 -> fund >= pending+0)
    task1, _, _ = await repo.create(topic_id, "Task 1")
    task2, _, _ = await repo.create(topic_id, "Task 2")

    # 3rd task: fund=2, pending=2, need 3 -> auto-cancel oldest
    task3, fund, error = await repo.create(topic_id, "Task 3")

    assert error is None
    assert task3 is not None

    # task1 should be auto-cancelled
    await session.refresh(task1)
    assert task1.status == BonusTaskStatus.CANCELLED

    # task2 and task3 should be pending
    await session.refresh(task2)
    assert task2.status == BonusTaskStatus.PENDING
    assert task3.status == BonusTaskStatus.PENDING


async def test_create_fails_zero_fund(session):
    """Create fails when fund has 0 slots (even after cancel attempt)."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=0)
    repo = BonusTaskRepository(session)

    task, fund, error = await repo.create(topic_id, "No room")

    assert task is None
    assert error is not None
    assert "Not enough" in error


async def test_create_fails_no_fund(session):
    """Create fails when bonus fund doesn't exist."""
    topic_id = await _create_topic(session)
    repo = BonusTaskRepository(session)

    task, fund, error = await repo.create(topic_id, "Orphan task")

    assert task is None
    assert fund is None
    assert "not found" in error.lower()


# ---- complete tests ----


async def test_complete_decrements_fund(session):
    """Completing a task deducts one slot from fund."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, _, _ = await repo.create(topic_id, "Task to complete")

    completed, updated_fund, error = await repo.complete(
        task.id, quality_notes="Well done"
    )

    assert error is None
    assert completed.status == BonusTaskStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.quality_notes == "Well done"
    assert updated_fund.available_tasks == 4  # 5 - 1


async def test_complete_fails_for_completed_task(session):
    """Cannot complete an already-completed task."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, _, _ = await repo.create(topic_id, "Task")
    await repo.complete(task.id)

    # Try again
    _, _, error = await repo.complete(task.id)
    assert error is not None
    assert "already" in error.lower()


async def test_complete_fails_for_cancelled_task(session):
    """Cannot complete a cancelled task."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, _, _ = await repo.create(topic_id, "Task")
    await repo.cancel(task.id)

    _, _, error = await repo.complete(task.id)
    assert error is not None
    assert "already" in error.lower()


# ---- cancel tests ----


async def test_cancel_pending_task(session):
    """Cancelling a pending task sets status to CANCELLED."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, _, _ = await repo.create(topic_id, "Task to cancel")
    cancelled, error = await repo.cancel(task.id)

    assert error is None
    assert cancelled.status == BonusTaskStatus.CANCELLED


async def test_cancel_fails_for_completed_task(session):
    """Cannot cancel an already-completed task."""
    topic_id = await _create_topic(session)
    await _create_fund(session, available_tasks=5)
    repo = BonusTaskRepository(session)

    task, _, _ = await repo.create(topic_id, "Task")
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
