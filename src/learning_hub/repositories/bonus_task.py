"""Repository for BonusTask model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus_task import BonusTask
from learning_hub.models.enums import BonusTaskStatus


class BonusTaskRepository:
    """Repository for BonusTask CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_topic_id: int,
        task_description: str,
        minutes_promised: int,
    ) -> BonusTask:
        """Create a new bonus task."""
        task = BonusTask(
            subject_topic_id=subject_topic_id,
            task_description=task_description,
            minutes_promised=minutes_promised,
            status=BonusTaskStatus.PROMISED,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: int) -> BonusTask | None:
        """Get bonus task by ID."""
        return await self.session.get(BonusTask, task_id)

    async def list(
        self,
        subject_topic_id: int | None = None,
        status: BonusTaskStatus | None = None,
    ) -> list[BonusTask]:
        """List bonus tasks with optional filters."""
        query = select(BonusTask)

        if subject_topic_id is not None:
            query = query.where(BonusTask.subject_topic_id == subject_topic_id)

        if status is not None:
            query = query.where(BonusTask.status == status)

        query = query.order_by(BonusTask.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def complete(
        self,
        task_id: int,
        quality_notes: str | None = None,
    ) -> BonusTask | None:
        """Mark task as completed. Returns None if not found."""
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        task.status = BonusTaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        if quality_notes is not None:
            task.quality_notes = quality_notes

        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def cancel(self, task_id: int) -> BonusTask | None:
        """Cancel a task. Returns None if not found."""
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        task.status = BonusTaskStatus.CANCELLED

        await self.session.commit()
        await self.session.refresh(task)
        return task
