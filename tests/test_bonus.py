"""Tests for Bonus repository: deduplication, validation, deletion protection."""

import pytest

from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.repositories.homework import HomeworkRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _setup_subject(session) -> int:
    """Create school + subject, return subject_id."""
    school = School(code="CZ", name="Czech School", is_active=True)
    session.add(school)
    await session.flush()
    subject = Subject(school_id=school.id, name="Math")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject.id


# ---- ad-hoc bonus tests ----


async def test_create_adhoc_with_reason(session):
    """Ad-hoc bonus with reason succeeds."""
    repo = BonusRepository(session)
    bonus = await repo.create(minutes=15, reason="Helped with cleaning")

    assert bonus.id is not None
    assert bonus.minutes == 15
    assert bonus.reason == "Helped with cleaning"
    assert bonus.homework_id is None
    assert bonus.rewarded is False


async def test_create_adhoc_without_reason_fails(session):
    """Ad-hoc bonus without reason raises ValueError."""
    repo = BonusRepository(session)

    with pytest.raises(ValueError, match="requires a reason"):
        await repo.create(minutes=10)


async def test_create_adhoc_empty_reason_fails(session):
    """Ad-hoc bonus with whitespace-only reason raises ValueError."""
    repo = BonusRepository(session)

    with pytest.raises(ValueError, match="requires a reason"):
        await repo.create(minutes=10, reason="   ")


async def test_create_adhoc_duplicate_within_window(session):
    """Ad-hoc bonus with same reason within 10 min is rejected."""
    repo = BonusRepository(session)

    await repo.create(minutes=10, reason="Good behavior")

    with pytest.raises(ValueError, match="Duplicate ad-hoc bonus"):
        await repo.create(minutes=10, reason="Good behavior")


async def test_create_adhoc_different_reasons_ok(session):
    """Ad-hoc bonuses with different reasons are fine."""
    repo = BonusRepository(session)

    b1 = await repo.create(minutes=10, reason="Good behavior")
    b2 = await repo.create(minutes=5, reason="Helped with dishes")

    assert b1.id != b2.id


async def test_create_adhoc_negative_minutes(session):
    """Ad-hoc bonus can have negative minutes (penalty)."""
    repo = BonusRepository(session)
    bonus = await repo.create(minutes=-10, reason="Broke a rule")
    assert bonus.minutes == -10


# ---- homework bonus tests ----


async def test_create_homework_bonus(session):
    """Homework-linked bonus succeeds."""
    subject_id = await _setup_subject(session)
    hw_repo = HomeworkRepository(session)
    hw = await hw_repo.create(subject_id=subject_id, description="Exercise 1")

    repo = BonusRepository(session)
    bonus = await repo.create(minutes=10, homework_id=hw.id)

    assert bonus.homework_id == hw.id
    assert bonus.minutes == 10


async def test_create_homework_bonus_duplicate(session):
    """Only one bonus per homework_id is allowed."""
    subject_id = await _setup_subject(session)
    hw_repo = HomeworkRepository(session)
    hw = await hw_repo.create(subject_id=subject_id, description="Exercise 1")

    repo = BonusRepository(session)
    await repo.create(minutes=10, homework_id=hw.id)

    with pytest.raises(ValueError, match="already has a bonus"):
        await repo.create(minutes=5, homework_id=hw.id)


# ---- delete tests ----


async def test_delete_unrewarded(session):
    """Unrewarded bonus can be deleted."""
    repo = BonusRepository(session)
    bonus = await repo.create(minutes=10, reason="Temporary")

    success, error = await repo.delete(bonus.id)
    assert success is True
    assert error is None


async def test_delete_rewarded_blocked(session):
    """Rewarded bonus cannot be deleted."""
    repo = BonusRepository(session)
    bonus = await repo.create(minutes=10, reason="Good stuff")

    # Mark as rewarded manually
    bonus.rewarded = True
    await session.commit()

    success, error = await repo.delete(bonus.id)
    assert success is False
    assert error is not None
    assert "rewarded" in error.lower()


async def test_delete_not_found(session):
    """Deleting non-existent bonus returns failure."""
    repo = BonusRepository(session)
    success, error = await repo.delete(999)
    assert success is False
    assert "not found" in error.lower()


# ---- list_unrewarded / mark_all_rewarded ----


async def test_list_unrewarded(session):
    """list_unrewarded returns only unrewarded bonuses."""
    repo = BonusRepository(session)

    b1 = await repo.create(minutes=10, reason="One")
    b2 = await repo.create(minutes=5, reason="Two")

    # Mark b1 as rewarded
    b1.rewarded = True
    await session.commit()

    unrewarded = await repo.list_unrewarded()
    assert len(unrewarded) == 1
    assert unrewarded[0].id == b2.id


async def test_mark_all_rewarded(session):
    """mark_all_rewarded flips all unrewarded to rewarded."""
    repo = BonusRepository(session)

    await repo.create(minutes=10, reason="Alpha")
    await repo.create(minutes=5, reason="Beta")

    count = await repo.mark_all_rewarded()
    assert count == 2

    unrewarded = await repo.list_unrewarded()
    assert len(unrewarded) == 0
