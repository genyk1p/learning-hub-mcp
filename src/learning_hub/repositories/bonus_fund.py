"""Repository for BonusFund model."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus_fund import BonusFund

FUND_ID = 1


class BonusFundRepository:
    """Repository for BonusFund CRUD operations (singleton fund, id=1)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, available_tasks: int = 0) -> BonusFund:
        """Create the singleton bonus fund (id=1)."""
        fund = BonusFund(id=FUND_ID, name=name, available_tasks=available_tasks)
        self.session.add(fund)
        await self.session.commit()
        await self.session.refresh(fund)
        return fund

    async def get(self) -> BonusFund | None:
        """Get the singleton bonus fund."""
        return await self.session.get(BonusFund, FUND_ID)

    async def add_tasks(self, count: int) -> tuple[BonusFund | None, int]:
        """Add available task slots to the fund.

        Returns:
            Tuple of (fund, available_before). Fund is None if not found.
        """
        fund = await self.get()
        if fund is None:
            return None, 0

        available_before = fund.available_tasks
        fund.available_tasks += count
        await self.session.commit()
        await self.session.refresh(fund)
        return fund, available_before
