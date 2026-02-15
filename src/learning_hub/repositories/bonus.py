"""Repository for Bonus model."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus import Bonus


class BonusRepository:
    """Repository for Bonus CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        homework_id: int,
        minutes: int,
    ) -> Bonus:
        """Create a new bonus."""
        bonus = Bonus(
            homework_id=homework_id,
            minutes=minutes,
        )
        self.session.add(bonus)
        await self.session.commit()
        await self.session.refresh(bonus)
        return bonus

    async def delete(self, bonus_id: int) -> bool:
        """Delete a bonus by ID. Returns True if deleted, False if not found."""
        bonus = await self.session.get(Bonus, bonus_id)
        if bonus is None:
            return False
        await self.session.delete(bonus)
        await self.session.commit()
        return True

    async def list_unrewarded(self) -> list[Bonus]:
        """List all bonuses with rewarded=False."""
        query = (
            select(Bonus)
            .where(Bonus.rewarded.is_(False))
            .order_by(Bonus.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_all_rewarded(self) -> int:
        """Set rewarded=True for all unrewarded bonuses. Returns count of updated rows."""
        stmt = (
            update(Bonus)
            .where(Bonus.rewarded.is_(False))
            .values(rewarded=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore[union-attr]
