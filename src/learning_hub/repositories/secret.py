"""Repository for Secret model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.secret import Secret


class SecretRepository:
    """Repository for Secret CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(self, key: str) -> Secret | None:
        """Get a secret entry by key."""
        query = select(Secret).where(Secret.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_value(self, key: str) -> str | None:
        """Get raw secret value by key. Returns None if not found or not set."""
        entry = await self.get_by_key(key)
        if entry is None:
            return None
        return entry.value

    async def set_value(self, key: str, value: str) -> Secret | None:
        """Set the value for an existing secret key. Returns None if key not found."""
        entry = await self.get_by_key(key)
        if entry is None:
            return None
        entry.value = value
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_all(self) -> list[Secret]:
        """List all secret entries ordered by key."""
        query = select(Secret).order_by(Secret.key.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
