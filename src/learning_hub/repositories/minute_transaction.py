"""Repository for MinuteTransaction model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.enums import TransactionType
from learning_hub.models.minute_transaction import MinuteTransaction


class MinuteTransactionRepository:
    """Repository for MinuteTransaction CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        minutes: int,
        type: TransactionType,
        description: str | None = None,
        grade_id: int | None = None,
        homework_id: int | None = None,
        bonus_task_id: int | None = None,
    ) -> MinuteTransaction:
        """Create a new minute transaction."""
        tx = MinuteTransaction(
            minutes=minutes,
            type=type.value,
            description=description,
            grade_id=grade_id,
            homework_id=homework_id,
            bonus_task_id=bonus_task_id,
        )
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    async def get_balance(self) -> int:
        """Return current balance as SUM of all transaction minutes."""
        query = select(func.coalesce(func.sum(MinuteTransaction.minutes), 0))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def list(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        type: str | None = None,
    ) -> list[MinuteTransaction]:
        """List transactions with optional filters."""
        query = select(MinuteTransaction).order_by(MinuteTransaction.created_at.desc())

        if date_from is not None:
            query = query.where(MinuteTransaction.created_at >= date_from)
        if date_to is not None:
            query = query.where(MinuteTransaction.created_at <= date_to)
        if type is not None:
            query = query.where(MinuteTransaction.type == type)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_homework_id(self, homework_id: int) -> MinuteTransaction | None:
        """Get transaction for a given homework (for idempotency checks)."""
        query = select(MinuteTransaction).where(
            MinuteTransaction.homework_id == homework_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_bonus_task_id(self, bonus_task_id: int) -> MinuteTransaction | None:
        """Get transaction for a given bonus task (for idempotency checks)."""
        query = select(MinuteTransaction).where(
            MinuteTransaction.bonus_task_id == bonus_task_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
