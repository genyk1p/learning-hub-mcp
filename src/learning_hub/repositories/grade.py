"""Repository for Grade model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from learning_hub.models.grade import Grade
from learning_hub.models.subject import Subject
from learning_hub.models.enums import GradeSource, GradeValue, SyncProviderType


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
        external_id: str | None = None,
        external_source: SyncProviderType | None = None,
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
            external_id=external_id,
            external_source=external_source.value if external_source else None,
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

    async def get_by_external_id(
        self, external_id: str, source: SyncProviderType
    ) -> Grade | None:
        """Get grade by external ID and source provider."""
        query = select(Grade).where(
            Grade.external_id == external_id,
            Grade.external_source == source.value,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        subject_id: int | None = None,
        school_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
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

        query = query.order_by(Grade.date.desc())

        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

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

    async def list_with_topics_since(self, since: datetime) -> list[Grade]:
        """List grades with linked topics since a given date, excluding grade 1.

        Used for fallback topic selection when no pending TopicReviews exist.
        Only returns grades where subject_topic_id is set and grade_value > 1.
        Eager-loads subject and subject_topic for building the response.
        """
        query = (
            select(Grade)
            .options(
                joinedload(Grade.subject),
                joinedload(Grade.subject_topic),
            )
            .where(Grade.date >= since)
            .where(Grade.subject_topic_id.isnot(None))
            .where(Grade.grade_value != GradeValue.EXCELLENT)
            .order_by(Grade.date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def mark_escalated(self, grade_ids: list[int]) -> int:
        """Set escalated_at to now for given grade IDs.

        Returns count of updated rows.
        """
        now = datetime.now()
        stmt = (
            update(Grade)
            .where(Grade.id.in_(grade_ids))
            .values(escalated_at=now)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore[union-attr]
