"""Tests for weekly game minutes calculation and week finalization."""

from collections import Counter
from datetime import datetime, timedelta

import pytest

from learning_hub.models.bonus import Bonus
from learning_hub.models.bonus_fund import BonusFund
from learning_hub.models.config_entry import ConfigEntry
from learning_hub.models.enums import GradeValue
from learning_hub.models.grade import Grade
from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.models.week import Week
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.repositories.bonus_fund import BonusFundRepository
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.week import WeekRepository


pytestmark = pytest.mark.asyncio

# Same default as in weeks.py
_DEFAULT_GRADE_MINUTES_MAP = {1: 15, 2: 10, 3: 0, 4: -20, 5: -25}


# ---- helpers ----


async def _create_school(session, code="CZ", name="Czech School") -> School:
    school = School(code=code, name=name, is_active=True)
    session.add(school)
    await session.commit()
    await session.refresh(school)
    return school


async def _create_subject(session, school_id: int, name="Math") -> Subject:
    subject = Subject(school_id=school_id, name=name)
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


async def _create_week(
    session,
    week_key: str,
    start_at: datetime,
    end_at: datetime,
    is_finalized: bool = False,
    carryover_out_minutes: int = 0,
    total_minutes: int = 0,
    penalty_minutes: int = 0,
) -> Week:
    week = Week(
        week_key=week_key,
        start_at=start_at,
        end_at=end_at,
        is_finalized=is_finalized,
        carryover_out_minutes=carryover_out_minutes,
        total_minutes=total_minutes,
        penalty_minutes=penalty_minutes,
    )
    session.add(week)
    await session.commit()
    await session.refresh(week)
    return week


async def _seed_grade_map_config(session) -> None:
    """Seed GRADE_MINUTES_MAP config entry (like Alembic migration does)."""
    entry = ConfigEntry(
        key="GRADE_MINUTES_MAP",
        value='{"1":15,"2":10,"3":0,"4":-20,"5":-25}',
        description="Grade to minutes map",
    )
    session.add(entry)
    await session.commit()


async def _create_bonus_fund(session, available_tasks: int = 0) -> BonusFund:
    fund = BonusFund(id=1, name="Test Fund", available_tasks=available_tasks)
    session.add(fund)
    await session.commit()
    await session.refresh(fund)
    return fund


async def _calculate(session, new_week_key: str, bonus_fund_topup: int = 15) -> dict:
    """Replicate calculate_weekly_minutes logic with the test session.

    This mirrors the tool's logic from weeks.py but uses the provided session
    instead of AsyncSessionLocal, making it testable.
    """
    week_repo = WeekRepository(session)
    grade_repo = GradeRepository(session)
    bonus_repo = BonusRepository(session)
    fund_repo = BonusFundRepository(session)
    config_repo = ConfigEntryRepository(session)

    new_week_date = datetime.fromisoformat(new_week_key).date()
    prev_week_date = new_week_date - timedelta(days=7)
    prev_week_key = prev_week_date.isoformat()

    # Read config
    grade_map_raw = await config_repo.get_json_value("GRADE_MINUTES_MAP")
    grade_minutes_map = (
        {int(k): v for k, v in grade_map_raw.items()}
        if isinstance(grade_map_raw, dict)
        else _DEFAULT_GRADE_MINUTES_MAP
    )

    # Step 1: check prev week finalized
    prev_week = await week_repo.get_by_key(prev_week_key)
    if prev_week is None or not prev_week.is_finalized:
        return {"status": "prev_week_not_finalized", "prev_week_key": prev_week_key}

    carry = prev_week.carryover_out_minutes

    # Step 2: check not already calculated
    existing = await week_repo.get_by_key(new_week_key)
    if existing is not None:
        return {"status": "already_calculated", "week_key": new_week_key}

    # Step 3: create new week
    start_at = prev_week.end_at
    end_at = start_at + timedelta(days=7)
    new_week = await week_repo.create(week_key=new_week_key, start_at=start_at, end_at=end_at)

    penalty_minutes = new_week.penalty_minutes

    # Step 4: get unrewarded grades for PREVIOUS week period
    grades = await grade_repo.list(
        date_from=prev_week.start_at,
        date_to=prev_week.end_at,
        rewarded=False,
    )

    # Step 5: calculate grade_minutes
    grade_minutes = 0
    grade_counter: Counter[int] = Counter()
    for grade in grades:
        gv = grade.grade_value.value
        minutes = grade_minutes_map.get(gv, 0)
        grade_minutes += minutes
        grade_counter[gv] += 1

    # Step 6: get unrewarded bonuses
    bonuses = await bonus_repo.list_unrewarded()
    homework_bonus_minutes = sum(b.minutes for b in bonuses)

    # Step 7: total
    total_minutes = carry + grade_minutes + homework_bonus_minutes - penalty_minutes

    # Step 8: update week
    new_week, _ = await week_repo.update(
        week_key=new_week_key,
        grade_minutes=grade_minutes,
        homework_bonus_minutes=homework_bonus_minutes,
        total_minutes=total_minutes,
    )

    # Step 9: mark grades rewarded
    grade_ids = [g.id for g in grades]
    grades_marked = await grade_repo.mark_rewarded(grade_ids)

    # Step 10: mark bonuses rewarded
    bonuses_marked = await bonus_repo.mark_all_rewarded()

    # Step 11: top up fund
    if bonus_fund_topup > 0:
        await fund_repo.add_tasks(bonus_fund_topup)

    return {
        "status": "ok",
        "carry_from_prev": carry,
        "grade_minutes": grade_minutes,
        "homework_bonus_minutes": homework_bonus_minutes,
        "penalty_minutes": penalty_minutes,
        "total_minutes": total_minutes,
        "grades_marked": grades_marked,
        "bonuses_marked": bonuses_marked,
    }


# ---- finalize tests ----


async def test_finalize_calculates_carryover(session):
    """Finalize sets carryover = total_minutes - actual_played_minutes."""
    await _create_week(
        session,
        "2026-02-14",
        datetime(2026, 2, 14, 8, 0),
        datetime(2026, 2, 21, 8, 0),
        total_minutes=50,
    )

    repo = WeekRepository(session)
    finalized = await repo.finalize("2026-02-14", actual_played_minutes=30)

    assert finalized is not None
    assert finalized.is_finalized is True
    assert finalized.actual_played_minutes == 30
    assert finalized.carryover_out_minutes == 20  # 50 - 30


async def test_finalize_negative_carryover(session):
    """If played more than total, carryover is negative."""
    await _create_week(
        session,
        "2026-02-14",
        datetime(2026, 2, 14, 8, 0),
        datetime(2026, 2, 21, 8, 0),
        total_minutes=30,
    )

    repo = WeekRepository(session)
    finalized = await repo.finalize("2026-02-14", actual_played_minutes=45)

    assert finalized.carryover_out_minutes == -15  # 30 - 45


async def test_finalize_idempotent(session):
    """Finalizing already-finalized week returns it as-is."""
    await _create_week(
        session,
        "2026-02-14",
        datetime(2026, 2, 14, 8, 0),
        datetime(2026, 2, 21, 8, 0),
        total_minutes=50,
        is_finalized=True,
        carryover_out_minutes=20,
    )

    repo = WeekRepository(session)
    # Try to finalize with different played minutes — should be ignored
    result = await repo.finalize("2026-02-14", actual_played_minutes=999)

    assert result.carryover_out_minutes == 20  # unchanged
    assert result.is_finalized is True


async def test_finalize_not_found(session):
    """Finalizing non-existent week returns None."""
    repo = WeekRepository(session)
    result = await repo.finalize("2099-01-01", actual_played_minutes=10)
    assert result is None


async def test_update_rejected_if_finalized(session):
    """Cannot update a finalized week."""
    await _create_week(
        session,
        "2026-02-14",
        datetime(2026, 2, 14, 8, 0),
        datetime(2026, 2, 21, 8, 0),
        is_finalized=True,
    )

    repo = WeekRepository(session)
    week, error = await repo.update("2026-02-14", grade_minutes=100)

    assert error is not None
    assert "finalized" in error.lower()
    assert week is not None  # returns current state


# ---- full calculation tests ----


async def test_calculate_full_flow(session):
    """Full calculation: grades + bonuses + carryover -> correct total."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=5)

    # Previous week: finalized with carryover=10
    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=10, total_minutes=40,
    )

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    # Grades within prev week period
    g1 = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.EXCELLENT,  # 1 -> +15
        date=datetime(2026, 2, 9, 10, 0),
        rewarded=False,
    )
    g2 = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.POOR,  # 4 -> -20
        date=datetime(2026, 2, 10, 10, 0),
        rewarded=False,
    )
    session.add_all([g1, g2])

    # Unrewarded bonus
    b1 = Bonus(minutes=10, reason="on-time homework", rewarded=False)
    session.add(b1)
    await session.commit()

    result = await _calculate(session, "2026-02-14")

    assert result["status"] == "ok"
    assert result["carry_from_prev"] == 10
    assert result["grade_minutes"] == -5  # 15 + (-20)
    assert result["homework_bonus_minutes"] == 10
    assert result["total_minutes"] == 15  # 10 + (-5) + 10 - 0


async def test_calculate_marks_grades_rewarded(session):
    """After calculation, processed grades must be marked rewarded."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    grade = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.GOOD,
        date=datetime(2026, 2, 9, 10, 0),
        rewarded=False,
    )
    session.add(grade)
    await session.commit()

    result = await _calculate(session, "2026-02-14")
    assert result["status"] == "ok"
    assert result["grades_marked"] == 1

    # Verify grade is now rewarded
    await session.refresh(grade)
    assert grade.rewarded is True


async def test_calculate_marks_bonuses_rewarded(session):
    """After calculation, processed bonuses must be marked rewarded."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    bonus = Bonus(minutes=15, reason="ad-hoc reward", rewarded=False)
    session.add(bonus)
    await session.commit()

    result = await _calculate(session, "2026-02-14")
    assert result["status"] == "ok"
    assert result["bonuses_marked"] == 1

    await session.refresh(bonus)
    assert bonus.rewarded is True


async def test_calculate_tops_up_bonus_fund(session):
    """Calculation should add topup slots to bonus fund."""
    await _seed_grade_map_config(session)
    fund = await _create_bonus_fund(session, available_tasks=3)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    result = await _calculate(session, "2026-02-14", bonus_fund_topup=10)
    assert result["status"] == "ok"

    await session.refresh(fund)
    assert fund.available_tasks == 13  # 3 + 10


async def test_calculate_prev_not_finalized(session):
    """If previous week not finalized, calculation is blocked."""
    await _seed_grade_map_config(session)

    # Previous week exists but NOT finalized
    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=False,
    )

    result = await _calculate(session, "2026-02-14")
    assert result["status"] == "prev_week_not_finalized"


async def test_calculate_prev_not_exists(session):
    """If previous week doesn't exist, calculation is blocked."""
    await _seed_grade_map_config(session)

    result = await _calculate(session, "2026-02-14")
    assert result["status"] == "prev_week_not_finalized"


async def test_calculate_already_calculated(session):
    """If new week already exists, calculation returns already_calculated."""
    await _seed_grade_map_config(session)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )
    # New week already exists
    await _create_week(
        session, "2026-02-14",
        datetime(2026, 2, 14, 8, 0),
        datetime(2026, 2, 21, 8, 0),
    )

    result = await _calculate(session, "2026-02-14")
    assert result["status"] == "already_calculated"


async def test_calculate_empty_week(session):
    """No grades and no bonuses -> total equals carryover."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=5,
    )

    result = await _calculate(session, "2026-02-14", bonus_fund_topup=0)
    assert result["status"] == "ok"
    assert result["grade_minutes"] == 0
    assert result["homework_bonus_minutes"] == 0
    assert result["total_minutes"] == 5  # just carryover


async def test_calculate_negative_total(session):
    """Bad grades can make total negative."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    # Two FAIL grades: 2 * (-25) = -50
    for day in (9, 11):
        session.add(Grade(
            subject_id=subject.id,
            grade_value=GradeValue.FAIL,
            date=datetime(2026, 2, day, 10, 0),
            rewarded=False,
        ))
    await session.commit()

    result = await _calculate(session, "2026-02-14", bonus_fund_topup=0)
    assert result["status"] == "ok"
    assert result["total_minutes"] == -50


async def test_calculate_uses_default_map_without_config(session):
    """If GRADE_MINUTES_MAP config is missing, fallback to defaults."""
    # Don't seed config — no GRADE_MINUTES_MAP entry
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    session.add(Grade(
        subject_id=subject.id,
        grade_value=GradeValue.EXCELLENT,  # 1 -> +15 from default map
        date=datetime(2026, 2, 9, 10, 0),
        rewarded=False,
    ))
    await session.commit()

    result = await _calculate(session, "2026-02-14", bonus_fund_topup=0)
    assert result["status"] == "ok"
    assert result["grade_minutes"] == 15


async def test_calculate_ignores_already_rewarded_grades(session):
    """Already-rewarded grades from a prior calculation are not double-counted."""
    await _seed_grade_map_config(session)
    await _create_bonus_fund(session, available_tasks=0)

    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session, "2026-02-07", prev_start, prev_end,
        is_finalized=True, carryover_out_minutes=0,
    )

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    # Already-rewarded grade (from previous calculation)
    session.add(Grade(
        subject_id=subject.id,
        grade_value=GradeValue.EXCELLENT,  # +15 if counted
        date=datetime(2026, 2, 9, 10, 0),
        rewarded=True,
    ))
    # New unrewarded grade
    session.add(Grade(
        subject_id=subject.id,
        grade_value=GradeValue.GOOD,  # +10
        date=datetime(2026, 2, 10, 10, 0),
        rewarded=False,
    ))
    await session.commit()

    result = await _calculate(session, "2026-02-14", bonus_fund_topup=0)
    assert result["status"] == "ok"
    assert result["grade_minutes"] == 10  # only the unrewarded GOOD grade
    assert result["grades_marked"] == 1
