"""Tests for preview_weekly_minutes tool logic."""

from collections import Counter
from datetime import datetime, timedelta

import pytest

from learning_hub.models.bonus import Bonus
from learning_hub.models.enums import GradeValue
from learning_hub.models.grade import Grade
from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.models.week import Week
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.week import WeekRepository


pytestmark = pytest.mark.asyncio

# Default grade-to-minutes map (same as in weeks.py)
_DEFAULT_GRADE_MINUTES_MAP = {1: 15, 2: 10, 3: 0, 4: -20, 5: -25}


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
    penalty_minutes: int = 0,
) -> Week:
    week = Week(
        week_key=week_key,
        start_at=start_at,
        end_at=end_at,
        is_finalized=is_finalized,
        carryover_out_minutes=carryover_out_minutes,
        penalty_minutes=penalty_minutes,
    )
    session.add(week)
    await session.commit()
    await session.refresh(week)
    return week


async def _preview(session, now: datetime) -> dict:
    """Run the preview logic directly (same as the tool, but using the test session)."""
    week_repo = WeekRepository(session)
    grade_repo = GradeRepository(session)
    bonus_repo = BonusRepository(session)
    config_repo = ConfigEntryRepository(session)

    current_week = await week_repo.get_current(now)
    if current_week is None:
        return {"status": "no_active_week"}

    prev_date = (
        datetime.fromisoformat(current_week.week_key).date()
        - timedelta(days=7)
    )
    prev_week_key = prev_date.isoformat()
    prev_week = await week_repo.get_by_key(prev_week_key)
    carry = (
        prev_week.carryover_out_minutes
        if prev_week and prev_week.is_finalized
        else 0
    )

    grade_map_raw = await config_repo.get_json_value("GRADE_MINUTES_MAP")
    grade_minutes_map = (
        {int(k): v for k, v in grade_map_raw.items()}
        if isinstance(grade_map_raw, dict)
        else _DEFAULT_GRADE_MINUTES_MAP
    )

    grades = await grade_repo.list(
        date_from=current_week.start_at,
        date_to=current_week.end_at,
        rewarded=False,
    )

    grade_minutes = 0
    grade_counter: Counter[int] = Counter()
    for grade in grades:
        gv = grade.grade_value.value
        minutes = grade_minutes_map.get(gv, 0)
        grade_minutes += minutes
        grade_counter[gv] += 1

    bonuses = await bonus_repo.list_unrewarded()
    homework_bonus_minutes = sum(b.minutes for b in bonuses)

    penalty_minutes = current_week.penalty_minutes
    total_minutes = carry + grade_minutes + homework_bonus_minutes - penalty_minutes

    return {
        "status": "preview",
        "week_key": current_week.week_key,
        "carry_from_prev": carry,
        "grade_minutes": grade_minutes,
        "homework_bonus_minutes": homework_bonus_minutes,
        "penalty_minutes": penalty_minutes,
        "total_minutes": total_minutes,
        "grades_count": len(grades),
        "bonuses_count": len(bonuses),
    }


async def test_preview_no_active_week(session):
    """No current week exists -> status='no_active_week'."""
    now = datetime(2026, 2, 18, 12, 0)
    result = await _preview(session, now)
    assert result["status"] == "no_active_week"


async def test_preview_with_grades_and_bonuses(session):
    """Active week with grades and bonuses -> correct calculation."""
    # Create week: Feb 14 (Sat) to Feb 21 (Sat)
    start = datetime(2026, 2, 14, 8, 0)
    end = datetime(2026, 2, 21, 8, 0)
    await _create_week(session, "2026-02-14", start, end)

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    # Add grades within the week period
    g1 = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.EXCELLENT,  # 1 -> +15
        date=datetime(2026, 2, 16, 10, 0),
        rewarded=False,
    )
    g2 = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.GOOD,  # 2 -> +10
        date=datetime(2026, 2, 17, 10, 0),
        rewarded=False,
    )
    session.add_all([g1, g2])

    # Add unrewarded bonus
    b1 = Bonus(minutes=10, reason="on-time homework", rewarded=False)
    session.add(b1)
    await session.commit()

    now = datetime(2026, 2, 18, 12, 0)
    result = await _preview(session, now)

    assert result["status"] == "preview"
    assert result["grade_minutes"] == 25  # 15 + 10
    assert result["homework_bonus_minutes"] == 10
    assert result["total_minutes"] == 35  # 0 + 25 + 10 - 0
    assert result["grades_count"] == 2
    assert result["bonuses_count"] == 1


async def test_preview_does_not_mutate(session):
    """Preview must not mark grades or bonuses as rewarded."""
    start = datetime(2026, 2, 14, 8, 0)
    end = datetime(2026, 2, 21, 8, 0)
    await _create_week(session, "2026-02-14", start, end)

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    grade = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.EXCELLENT,
        date=datetime(2026, 2, 16, 10, 0),
        rewarded=False,
    )
    session.add(grade)

    bonus = Bonus(minutes=5, reason="test bonus", rewarded=False)
    session.add(bonus)
    await session.commit()

    now = datetime(2026, 2, 18, 12, 0)
    result = await _preview(session, now)
    assert result["status"] == "preview"

    # Verify grades and bonuses are still unrewarded
    await session.refresh(grade)
    await session.refresh(bonus)
    assert grade.rewarded is False
    assert bonus.rewarded is False


async def test_preview_empty_week(session):
    """Active week with no grades or bonuses -> all zeros."""
    start = datetime(2026, 2, 14, 8, 0)
    end = datetime(2026, 2, 21, 8, 0)
    await _create_week(session, "2026-02-14", start, end)

    now = datetime(2026, 2, 18, 12, 0)
    result = await _preview(session, now)

    assert result["status"] == "preview"
    assert result["grade_minutes"] == 0
    assert result["homework_bonus_minutes"] == 0
    assert result["carry_from_prev"] == 0
    assert result["total_minutes"] == 0


async def test_preview_with_carryover(session):
    """Previous finalized week -> carryover is included."""
    # Previous week: Feb 7 to Feb 14, finalized with carryover
    prev_start = datetime(2026, 2, 7, 8, 0)
    prev_end = datetime(2026, 2, 14, 8, 0)
    await _create_week(
        session,
        "2026-02-07",
        prev_start,
        prev_end,
        is_finalized=True,
        carryover_out_minutes=20,
    )

    # Current week: Feb 14 to Feb 21
    start = datetime(2026, 2, 14, 8, 0)
    end = datetime(2026, 2, 21, 8, 0)
    await _create_week(session, "2026-02-14", start, end)

    school = await _create_school(session)
    subject = await _create_subject(session, school.id)

    grade = Grade(
        subject_id=subject.id,
        grade_value=GradeValue.POOR,  # 4 -> -20
        date=datetime(2026, 2, 16, 10, 0),
        rewarded=False,
    )
    session.add(grade)
    await session.commit()

    now = datetime(2026, 2, 18, 12, 0)
    result = await _preview(session, now)

    assert result["status"] == "preview"
    assert result["carry_from_prev"] == 20
    assert result["grade_minutes"] == -20
    assert result["total_minutes"] == 0  # 20 + (-20) + 0 - 0
