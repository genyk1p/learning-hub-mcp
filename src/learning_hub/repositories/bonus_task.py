"""Repository for BonusTask model."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus_task import BonusTask
from learning_hub.models.enums import BonusTaskStatus


class BonusTaskRepository:
    """Repository for BonusTask CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count_pending(self) -> int:
        """Count bonus tasks with PENDING status."""
        query = (
            select(func.count())
            .select_from(BonusTask)
            .where(BonusTask.status == BonusTaskStatus.PENDING)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def cancel_stale_pending(self, max_age_days: int = 7) -> list[BonusTask]:
        """Cancel pending tasks older than max_age_days.

        This prevents old unfinished tasks from blocking new task creation.
        Called automatically before creating a new task.
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)
        query = (
            select(BonusTask)
            .where(BonusTask.status == BonusTaskStatus.PENDING)
            .where(BonusTask.created_at < cutoff)
        )
        result = await self.session.execute(query)
        stale = list(result.scalars().all())
        for task in stale:
            task.status = BonusTaskStatus.CANCELLED
        if stale:
            await self.session.flush()
        return stale

    async def count_completed_since(self, since: datetime) -> int:
        """Count completed tasks since a given datetime."""
        query = (
            select(func.count())
            .select_from(BonusTask)
            .where(BonusTask.status == BonusTaskStatus.COMPLETED)
            .where(BonusTask.completed_at >= since)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_pending(self) -> int:
        """Count bonus tasks with PENDING status (public wrapper)."""
        return await self._count_pending()

    async def create(
        self,
        subject_topic_id: int,
        task_description: str,
    ) -> BonusTask:
        """Create a new bonus task. No business logic — just CRUD.

        Callers are responsible for checking limits and cancelling stale tasks
        before calling this method.
        """
        task = BonusTask(
            subject_topic_id=subject_topic_id,
            task_description=task_description,
            status=BonusTaskStatus.PENDING,
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
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int | None = None,
        order_asc: bool = False,
    ) -> list[BonusTask]:
        """List bonus tasks with optional filters."""
        query = select(BonusTask)

        if subject_topic_id is not None:
            query = query.where(BonusTask.subject_topic_id == subject_topic_id)

        if status is not None:
            query = query.where(BonusTask.status == status)

        if created_from is not None:
            query = query.where(BonusTask.created_at >= created_from)

        if created_to is not None:
            query = query.where(BonusTask.created_at < created_to)

        if order_asc:
            query = query.order_by(BonusTask.created_at.asc())
        else:
            query = query.order_by(BonusTask.created_at.desc())

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def complete(
        self,
        task_id: int,
        quality_notes: str | None = None,
    ) -> tuple[BonusTask | None, str | None]:
        """Mark task as completed.

        Always accepts — limits were checked at creation time.

        Returns:
            Tuple of (task, error). If error is not None, operation failed.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None, "Task not found"

        if task.status != BonusTaskStatus.PENDING:
            return task, f"Task is already {task.status.value}"

        task.status = BonusTaskStatus.COMPLETED
        task.completed_at = datetime.now()
        if quality_notes is not None:
            task.quality_notes = quality_notes

        await self.session.commit()
        await self.session.refresh(task)
        return task, None

    async def cancel(self, task_id: int) -> tuple[BonusTask | None, str | None]:
        """Cancel a task. Only PENDING tasks can be cancelled.

        Returns:
            Tuple of (task, error). If error is not None, operation failed.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None, "Task not found"

        if task.status != BonusTaskStatus.PENDING:
            return task, f"Task is already {task.status.value}"

        task.status = BonusTaskStatus.CANCELLED

        await self.session.commit()
        await self.session.refresh(task)
        return task, None
