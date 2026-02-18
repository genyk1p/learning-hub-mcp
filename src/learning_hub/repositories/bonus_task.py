"""Repository for BonusTask model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus_task import BonusTask
from learning_hub.models.bonus_fund import BonusFund
from learning_hub.models.enums import BonusTaskStatus

FUND_ID = 1


class BonusTaskRepository:
    """Repository for BonusTask CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_fund(self) -> BonusFund | None:
        """Get the singleton bonus fund."""
        return await self.session.get(BonusFund, FUND_ID)

    async def _count_pending(self) -> int:
        """Count bonus tasks with PENDING status."""
        query = (
            select(func.count())
            .select_from(BonusTask)
            .where(BonusTask.status == BonusTaskStatus.PENDING)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def _get_oldest_pending(self) -> BonusTask | None:
        """Get the oldest pending bonus task."""
        query = (
            select(BonusTask)
            .where(BonusTask.status == BonusTaskStatus.PENDING)
            .order_by(BonusTask.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        subject_topic_id: int,
        task_description: str,
    ) -> tuple[BonusTask | None, BonusFund | None, str | None]:
        """Create a new bonus task.

        Validates that fund has enough slots for all pending tasks + this new one.
        Does NOT deduct from fund - that happens on completion.

        Returns:
            Tuple of (task, fund, error). If error is not None, creation failed.
        """
        fund = await self._get_fund()
        if fund is None:
            return None, None, "Bonus fund not found. Create it first."

        pending_count = await self._count_pending()

        # If we're at or near the limit, cancel the oldest pending task to free a slot
        if pending_count > 0 and fund.available_tasks < pending_count + 1:
            oldest = await self._get_oldest_pending()
            if oldest is not None:
                oldest.status = BonusTaskStatus.CANCELLED
                await self.session.flush()
                pending_count -= 1

        needed = pending_count + 1

        if fund.available_tasks < needed:
            return None, fund, (
                f"Not enough task slots in fund. "
                f"Available: {fund.available_tasks}, "
                f"pending tasks: {pending_count}, "
                f"need at least {needed} to create a new one."
            )

        task = BonusTask(
            subject_topic_id=subject_topic_id,
            task_description=task_description,
            fund_id=FUND_ID,
            status=BonusTaskStatus.PENDING,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task, fund, None

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
    ) -> tuple[BonusTask | None, BonusFund | None, str | None]:
        """Mark task as completed and deduct one slot from fund.

        Returns:
            Tuple of (task, fund, error). If error is not None, operation failed.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None, None, "Task not found"

        fund = await self._get_fund()
        if fund is None:
            return None, None, "Bonus fund not found"

        # Deduct one task slot from fund
        fund.available_tasks -= 1

        # Mark task as completed
        task.status = BonusTaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        if quality_notes is not None:
            task.quality_notes = quality_notes

        await self.session.commit()
        await self.session.refresh(task)
        await self.session.refresh(fund)
        return task, fund, None

    async def cancel(self, task_id: int) -> BonusTask | None:
        """Cancel a task. Returns None if not found."""
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        task.status = BonusTaskStatus.CANCELLED

        await self.session.commit()
        await self.session.refresh(task)
        return task
