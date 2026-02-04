"""Repository for Homework model."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.homework import Homework
from learning_hub.models.enums import HomeworkStatus, GradeValue


class HomeworkRepository:
    """Repository for Homework CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_id: int,
        description: str,
        subject_topic_id: int | None = None,
        assigned_at: datetime | None = None,
        deadline_at: datetime | None = None,
        edupage_id: str | None = None,
    ) -> Homework:
        """Create a new homework."""
        homework = Homework(
            subject_id=subject_id,
            description=description,
            subject_topic_id=subject_topic_id,
            assigned_at=assigned_at,
            deadline_at=deadline_at,
            status=HomeworkStatus.PENDING,
            edupage_id=edupage_id,
        )
        self.session.add(homework)
        await self.session.commit()
        await self.session.refresh(homework)
        return homework

    async def get_by_id(self, homework_id: int) -> Homework | None:
        """Get homework by ID."""
        return await self.session.get(Homework, homework_id)

    async def get_by_edupage_id(self, edupage_id: str) -> Homework | None:
        """Get homework by EduPage ID."""
        query = select(Homework).where(Homework.edupage_id == edupage_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        subject_id: int | None = None,
        status: HomeworkStatus | None = None,
    ) -> list[Homework]:
        """List homeworks with optional filters."""
        query = select(Homework)

        if subject_id is not None:
            query = query.where(Homework.subject_id == subject_id)

        if status is not None:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.deadline_at.asc().nullslast())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_approaching_deadline(
        self,
        delta: timedelta,
    ) -> list[Homework]:
        """List pending homeworks with deadline within given delta from now."""
        now = datetime.now(timezone.utc)
        deadline_threshold = now + delta

        query = select(Homework).where(
            Homework.status == HomeworkStatus.PENDING,
            Homework.deadline_at.is_not(None),
            Homework.deadline_at > now,
            Homework.deadline_at <= deadline_threshold,
        ).order_by(Homework.deadline_at.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_overdue_without_penalty(self) -> list[Homework]:
        """List overdue homeworks where penalty was not yet applied."""
        now = datetime.now(timezone.utc)

        query = select(Homework).where(
            Homework.status == HomeworkStatus.PENDING,
            Homework.deadline_at < now,
            Homework.penalty_applied == False,
        ).order_by(Homework.deadline_at.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def complete(self, homework_id: int) -> Homework | None:
        """Mark homework as completed. Returns None if not found."""
        homework = await self.get_by_id(homework_id)
        if homework is None:
            return None

        homework.status = HomeworkStatus.DONE
        homework.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(homework)
        return homework

    async def update(
        self,
        homework_id: int,
        description: str | None = None,
        deadline_at: datetime | None = None,
        recommended_grade: GradeValue | None = None,
        penalty_applied: bool | None = None,
    ) -> Homework | None:
        """Update homework fields. Returns None if not found."""
        homework = await self.get_by_id(homework_id)
        if homework is None:
            return None

        if description is not None:
            homework.description = description
        if deadline_at is not None:
            homework.deadline_at = deadline_at
        if recommended_grade is not None:
            homework.recommended_grade = recommended_grade
        if penalty_applied is not None:
            homework.penalty_applied = penalty_applied

        await self.session.commit()
        await self.session.refresh(homework)
        return homework
