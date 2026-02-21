"""Repository for Bonus model."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.bonus import Bonus

# Dedup window for ad-hoc bonuses with the same reason
_ADHOC_DEDUP_MINUTES = 10


class BonusRepository:
    """Repository for Bonus CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        minutes: int,
        homework_id: int | None = None,
        reason: str | None = None,
    ) -> Bonus:
        """Create a new bonus. Ad-hoc bonuses (no homework_id) require a reason."""
        if reason:
            reason = reason.strip()

        if homework_id is None and not reason:
            raise ValueError("Ad-hoc bonus (no homework_id) requires a reason.")

        # Dedup: reject ad-hoc bonus with same reason within last N minutes
        if homework_id is None and reason:
            cutoff = datetime.now() - timedelta(minutes=_ADHOC_DEDUP_MINUTES)
            query = select(Bonus).where(
                Bonus.homework_id.is_(None),
                Bonus.reason == reason,
                Bonus.created_at >= cutoff,
            )
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            if existing is not None:
                raise ValueError(
                    f"Duplicate ad-hoc bonus: same reason was used {_ADHOC_DEDUP_MINUTES} min ago "
                    f"(bonus id={existing.id})."
                )

        # Check unique homework_id before insert
        if homework_id is not None:
            existing_query = select(Bonus).where(Bonus.homework_id == homework_id)
            result = await self.session.execute(existing_query)
            if result.scalar_one_or_none() is not None:
                raise ValueError(f"Homework {homework_id} already has a bonus record.")

        bonus = Bonus(
            homework_id=homework_id,
            minutes=minutes,
            reason=reason,
        )
        self.session.add(bonus)
        await self.session.commit()
        await self.session.refresh(bonus)
        return bonus

    async def delete(self, bonus_id: int) -> tuple[bool, str | None]:
        """Delete a bonus by ID. Rewarded bonuses cannot be deleted.

        Returns:
            Tuple of (success, error). If error is not None, deletion was rejected.
        """
        bonus = await self.session.get(Bonus, bonus_id)
        if bonus is None:
            return False, "Bonus not found"
        if bonus.rewarded:
            return False, "Cannot delete a rewarded bonus — already counted in weekly calculation."
        await self.session.delete(bonus)
        await self.session.commit()
        return True, None

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
