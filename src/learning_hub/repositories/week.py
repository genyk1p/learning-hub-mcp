"""Repository for Week model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.week import Week


class WeekRepository:
    """Repository for Week CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        week_key: str,
        start_at: datetime,
        end_at: datetime,
    ) -> Week:
        """Create a new week."""
        week = Week(
            week_key=week_key,
            start_at=start_at,
            end_at=end_at,
        )
        self.session.add(week)
        await self.session.commit()
        await self.session.refresh(week)
        return week

    async def get_by_key(self, week_key: str) -> Week | None:
        """Get week by key (e.g. '2026-02-01')."""
        query = select(Week).where(Week.week_key == week_key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_current(self, now: datetime) -> Week | None:
        """Get week that contains given datetime."""
        query = select(Week).where(
            Week.start_at <= now,
            Week.end_at > now,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        week_key: str,
        grade_minutes: int | None = None,
        homework_bonus_minutes: int | None = None,
        penalty_minutes: int | None = None,
        carryover_out_minutes: int | None = None,
        actual_played_minutes: int | None = None,
        total_minutes: int | None = None,
    ) -> tuple[Week | None, str | None]:
        """Update week fields.

        Returns:
            Tuple of (week, error). If error is not None, update was rejected.
        """
        week = await self.get_by_key(week_key)
        if week is None:
            return None, "Week not found"

        if week.is_finalized:
            return week, "Week is already finalized. Use create_bonus for ad-hoc adjustments."

        if grade_minutes is not None:
            week.grade_minutes = grade_minutes
        if homework_bonus_minutes is not None:
            week.homework_bonus_minutes = homework_bonus_minutes
        if penalty_minutes is not None:
            week.penalty_minutes = penalty_minutes
        if carryover_out_minutes is not None:
            week.carryover_out_minutes = carryover_out_minutes
        if actual_played_minutes is not None:
            week.actual_played_minutes = actual_played_minutes
        if total_minutes is not None:
            week.total_minutes = total_minutes

        await self.session.commit()
        await self.session.refresh(week)
        return week, None

    async def finalize(self, week_key: str, actual_played_minutes: int) -> Week | None:
        """Finalize week: save played minutes, calculate total, mark as finalized."""
        week = await self.get_by_key(week_key)
        if week is None:
            return None

        if week.is_finalized:
            return week

        week.actual_played_minutes = actual_played_minutes
        week.carryover_out_minutes = week.total_minutes - actual_played_minutes
        week.is_finalized = True

        await self.session.commit()
        await self.session.refresh(week)
        return week
