"""Repository for BonusFund model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus_fund import BonusFund


class BonusFundRepository:
    """Repository for BonusFund CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, minutes: int = 0) -> BonusFund:
        """Create a new bonus fund."""
        fund = BonusFund(name=name, minutes=minutes)
        self.session.add(fund)
        await self.session.commit()
        await self.session.refresh(fund)
        return fund

    async def get_by_id(self, fund_id: int) -> BonusFund | None:
        """Get fund by ID."""
        return await self.session.get(BonusFund, fund_id)

    async def list(self) -> list[BonusFund]:
        """List all bonus funds."""
        query = select(BonusFund).order_by(BonusFund.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def rename(self, fund_id: int, name: str) -> BonusFund | None:
        """Rename the fund. Returns None if not found."""
        fund = await self.get_by_id(fund_id)
        if fund is None:
            return None

        fund.name = name
        await self.session.commit()
        await self.session.refresh(fund)
        return fund

    async def add_minutes(self, fund_id: int, minutes: int) -> tuple[BonusFund | None, int]:
        """Add minutes to the fund balance.

        Returns:
            Tuple of (fund, minutes_before). Fund is None if not found.
        """
        fund = await self.get_by_id(fund_id)
        if fund is None:
            return None, 0

        minutes_before = fund.minutes
        fund.minutes += minutes
        await self.session.commit()
        await self.session.refresh(fund)
        return fund, minutes_before
