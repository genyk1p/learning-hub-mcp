"""Tests for homework completion and overdue logic."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select, func

from learning_hub.models.bonus import Bonus
from learning_hub.models.enums import HomeworkStatus, GradeValue
from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.repositories.homework import HomeworkRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _create_school(session) -> School:
    school = School(code="CZ", name="Czech School", is_active=True)
    session.add(school)
    await session.commit()
    await session.refresh(school)
    return school


async def _create_subject(session, school_id: int) -> Subject:
    subject = Subject(school_id=school_id, name="Math")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


async def _setup(session) -> int:
    """Create school + subject, return subject_id."""
    school = await _create_school(session)
    subject = await _create_subject(session, school.id)
    return subject.id


# ---- complete() tests ----


async def test_complete_ontime(session):
    """Homework completed before deadline -> DONE + positive bonus."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    # Deadline in the future
    hw = await repo.create(
        subject_id=subject_id,
        description="Solve problems 1-5",
        deadline_at=datetime.now() + timedelta(hours=24),
    )

    completed = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)

    assert completed is not None
    assert completed.status == HomeworkStatus.DONE
    assert completed.completed_at is not None

    # Check bonus was created
    result = await session.execute(
        select(Bonus).where(Bonus.homework_id == hw.id)
    )
    bonus = result.scalar_one()
    assert bonus.minutes == 10
    assert bonus.rewarded is False


async def test_complete_overdue(session):
    """Homework completed after deadline -> OVERDUE + negative bonus."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    # Deadline in the past
    hw = await repo.create(
        subject_id=subject_id,
        description="Solve problems 1-5",
        deadline_at=datetime.now() - timedelta(hours=2),
    )

    completed = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)

    assert completed.status == HomeworkStatus.OVERDUE

    result = await session.execute(
        select(Bonus).where(Bonus.homework_id == hw.id)
    )
    bonus = result.scalar_one()
    assert bonus.minutes == -10


async def test_complete_no_deadline(session):
    """Homework without deadline -> always on-time (DONE)."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Read chapter 3",
        deadline_at=None,
    )

    completed = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)

    assert completed.status == HomeworkStatus.DONE

    result = await session.execute(
        select(Bonus).where(Bonus.homework_id == hw.id)
    )
    bonus = result.scalar_one()
    assert bonus.minutes == 10


async def test_complete_idempotent_done(session):
    """Completing already-DONE homework returns it as-is (no duplicate bonus)."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Essay",
        deadline_at=datetime.now() + timedelta(hours=24),
    )

    # First completion
    await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)

    # Second completion — should be no-op
    result = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)
    assert result.status == HomeworkStatus.DONE

    # Only one bonus should exist
    count_result = await session.execute(
        select(func.count()).select_from(Bonus).where(Bonus.homework_id == hw.id)
    )
    assert count_result.scalar_one() == 1


async def test_complete_idempotent_overdue(session):
    """Completing already-OVERDUE homework returns it as-is."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Exercise",
        deadline_at=datetime.now() - timedelta(hours=2),
    )

    await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)
    result = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)

    assert result.status == HomeworkStatus.OVERDUE


async def test_complete_updates_existing_bonus(session):
    """If bonus for homework already exists, complete() updates its minutes."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Project",
        deadline_at=datetime.now() + timedelta(hours=24),
    )

    # Pre-create a bonus for this homework (e.g. from a different workflow)
    existing_bonus = Bonus(homework_id=hw.id, minutes=999, rewarded=False)
    session.add(existing_bonus)
    await session.commit()

    completed = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)
    assert completed.status == HomeworkStatus.DONE

    # Bonus should be updated, not duplicated
    await session.refresh(existing_bonus)
    assert existing_bonus.minutes == 10


async def test_complete_resets_rewarded_on_existing_bonus(session):
    """If bonus was already rewarded, complete() resets it to unrewarded."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Project v2",
        deadline_at=datetime.now() + timedelta(hours=24),
    )

    # Pre-create a REWARDED bonus
    existing_bonus = Bonus(homework_id=hw.id, minutes=999, rewarded=True)
    session.add(existing_bonus)
    await session.commit()

    completed = await repo.complete(hw.id, ontime_bonus=10, overdue_penalty=-10)
    assert completed.status == HomeworkStatus.DONE

    await session.refresh(existing_bonus)
    assert existing_bonus.minutes == 10
    assert existing_bonus.rewarded is False  # must be reset


async def test_complete_with_recommended_grade(session):
    """Complete stores recommended_grade on the homework."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="Test prep",
        deadline_at=datetime.now() + timedelta(hours=24),
    )

    completed = await repo.complete(
        hw.id,
        ontime_bonus=10,
        overdue_penalty=-10,
        recommended_grade=GradeValue.GOOD,
    )

    assert completed.recommended_grade == GradeValue.GOOD


async def test_complete_not_found(session):
    """Completing non-existent homework returns None."""
    repo = HomeworkRepository(session)
    result = await repo.complete(999)
    assert result is None


# ---- close_overdue() tests ----


async def test_close_overdue_batch(session):
    """close_overdue closes all pending homeworks past deadline with bonuses."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    past = datetime.now() - timedelta(hours=2)
    future = datetime.now() + timedelta(hours=24)

    hw_overdue1 = await repo.create(
        subject_id=subject_id,
        description="Overdue 1",
        deadline_at=past,
    )
    hw_overdue2 = await repo.create(
        subject_id=subject_id,
        description="Overdue 2",
        deadline_at=past - timedelta(hours=1),
    )
    hw_ontime = await repo.create(
        subject_id=subject_id,
        description="Still on time",
        deadline_at=future,
    )

    closed = await repo.close_overdue(ontime_bonus=10, overdue_penalty=-10)

    assert len(closed) == 2
    assert all(hw.status == HomeworkStatus.OVERDUE for hw in closed)

    # on-time homework should stay pending
    await session.refresh(hw_ontime)
    assert hw_ontime.status == HomeworkStatus.PENDING

    # Penalty bonuses must be created for each overdue homework
    bonus_count = await session.execute(
        select(func.count()).select_from(Bonus).where(
            Bonus.homework_id.in_([hw_overdue1.id, hw_overdue2.id])
        )
    )
    assert bonus_count.scalar_one() == 2

    # Verify penalty minutes
    result = await session.execute(
        select(Bonus).where(Bonus.homework_id == hw_overdue1.id)
    )
    assert result.scalar_one().minutes == -10


async def test_close_overdue_ignores_no_deadline(session):
    """Homeworks without deadline are not affected by close_overdue."""
    subject_id = await _setup(session)
    repo = HomeworkRepository(session)

    hw = await repo.create(
        subject_id=subject_id,
        description="No deadline",
        deadline_at=None,
    )

    closed = await repo.close_overdue()
    assert len(closed) == 0

    await session.refresh(hw)
    assert hw.status == HomeworkStatus.PENDING
