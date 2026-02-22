"""Repository for SyncProvider model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from learning_hub.models.sync_provider import SyncProvider


class SyncProviderRepository:
    """Repository for SyncProvider CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, provider_id: int) -> SyncProvider | None:
        """Get a sync provider by ID, eager-loading school."""
        query = (
            select(SyncProvider)
            .options(joinedload(SyncProvider.school))
            .where(SyncProvider.id == provider_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> SyncProvider | None:
        """Get a sync provider by code, eager-loading school."""
        query = (
            select(SyncProvider)
            .options(joinedload(SyncProvider.school))
            .where(SyncProvider.code == code)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[SyncProvider]:
        """List all sync providers ordered by code, eager-loading school."""
        query = (
            select(SyncProvider)
            .options(joinedload(SyncProvider.school))
            .order_by(SyncProvider.code.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_active(self) -> list[SyncProvider]:
        """List all active sync providers, eager-loading school."""
        query = (
            select(SyncProvider)
            .options(joinedload(SyncProvider.school))
            .where(SyncProvider.is_active == True)  # noqa: E712
            .order_by(SyncProvider.code.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        provider_id: int,
        is_active: bool | None = None,
        school_id: int | None = None,
        clear_school: bool = False,
    ) -> SyncProvider | None:
        """Update a sync provider.

        Args:
            provider_id: ID of the provider to update.
            is_active: New active status (optional).
            school_id: New school ID to link (optional).
            clear_school: Set school_id to NULL (optional).

        Returns:
            Updated provider or None if not found.

        Raises:
            ValueError: If resulting state would be active without a school.
        """
        provider = await self.get_by_id(provider_id)
        if provider is None:
            return None

        if school_id is not None:
            provider.school_id = school_id
        elif clear_school:
            provider.school_id = None

        if is_active is not None:
            provider.is_active = is_active

        # Validate: active provider must have a school
        if provider.is_active and provider.school_id is None:
            raise ValueError(
                f"Cannot activate provider '{provider.code}' without a linked school. "
                "Set school_id first."
            )

        await self.session.commit()
        await self.session.refresh(provider)
        return provider
