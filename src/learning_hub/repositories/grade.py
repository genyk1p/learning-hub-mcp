"""Repository for Grade model."""

from __future__ import annotations

from datetime import datetime

from datetime import timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from learning_hub.models.grade import Grade
from learning_hub.models.subject import Subject
from learning_hub.models.enums import GradeSource, GradeValue


class GradeRepository:
    """Repository for Grade CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_id: int,
        grade_value: GradeValue,
        date: datetime,
        subject_topic_id: int | None = None,
        bonus_task_id: int | None = None,
        homework_id: int | None = None,
        edupage_id: int | None = None,
        source: GradeSource = GradeSource.MANUAL,
        original_value: str | None = None,
    ) -> Grade:
        """Create a new grade.

        Raises ValueError if a grade for the same bonus_task_id already exists.
        """
        if bonus_task_id is not None:
            existing = await self._get_by_bonus_task_id(bonus_task_id)
            if existing is not None:
                raise ValueError(
                    f"Grade already exists for bonus_task_id={bonus_task_id} "
                    f"(grade id={existing.id})"
                )

        grade = Grade(
            subject_id=subject_id,
            grade_value=grade_value,
            date=date,
            subject_topic_id=subject_topic_id,
            bonus_task_id=bonus_task_id,
            homework_id=homework_id,
            edupage_id=edupage_id,
            source=source,
            original_value=original_value,
        )
        self.session.add(grade)
        await self.session.commit()
        await self.session.refresh(grade)
        return grade

    async def _get_by_bonus_task_id(self, bonus_task_id: int) -> Grade | None:
        """Get grade by bonus_task_id (for uniqueness check)."""
        query = select(Grade).where(Grade.bonus_task_id == bonus_task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, grade_id: int) -> Grade | None:
        """Get grade by ID."""
        return await self.session.get(Grade, grade_id)

    async def get_by_edupage_id(self, edupage_id: int) -> Grade | None:
        """Get grade by EduPage event_id."""
        query = select(Grade).where(Grade.edupage_id == edupage_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        subject_id: int | None = None,
        school_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        rewarded: bool | None = None,
    ) -> list[Grade]:
        """List grades with optional filters."""
        query = select(Grade).options(joinedload(Grade.subject))

        if subject_id is not None:
            query = query.where(Grade.subject_id == subject_id)

        if school_id is not None:
            query = query.join(Subject).where(Subject.school_id == school_id)

        if date_from is not None:
            query = query.where(Grade.date >= date_from)

        if date_to is not None:
            query = query.where(Grade.date <= date_to)

        if rewarded is not None:
            query = query.where(Grade.rewarded == rewarded)

        query = query.order_by(Grade.date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def update(
        self,
        grade_id: int,
        rewarded: bool | None = None,
    ) -> Grade | None:
        """Update grade fields. Returns None if not found."""
        grade = await self.get_by_id(grade_id)
        if grade is None:
            return None

        if rewarded is not None:
            grade.rewarded = rewarded

        await self.session.commit()
        await self.session.refresh(grade)
        return grade

    async def list_pending_escalation(self, threshold: int) -> list[Grade]:
        """List auto-synced grades that need escalation.

        Returns grades where source=AUTO, grade_value >= threshold,
        and escalated_at is NULL. Manual grades are excluded.
        Eager-loads subject and subject_topic for full context.
        """
        bad_grades = [g for g in GradeValue if g.value >= threshold]
        query = (
            select(Grade)
            .options(
                joinedload(Grade.subject).joinedload(Subject.school),
                joinedload(Grade.subject_topic),
            )
            .where(Grade.escalated_at.is_(None))
            .where(Grade.grade_value.in_(bad_grades))
            .where(Grade.source == GradeSource.AUTO)
            .order_by(Grade.date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def mark_rewarded(self, grade_ids: list[int]) -> int:
        """Set rewarded=True for given grade IDs. Returns count of updated rows."""
        if not grade_ids:
            return 0
        stmt = (
            update(Grade)
            .where(Grade.id.in_(grade_ids))
            .values(rewarded=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore[union-attr]

    async def mark_escalated(self, grade_ids: list[int]) -> int:
        """Set escalated_at to now for given grade IDs.

        Returns count of updated rows.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Grade)
            .where(Grade.id.in_(grade_ids))
            .values(escalated_at=now)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore[union-attr]
