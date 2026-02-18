"""Repository for ConfigEntry model."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.config_entry import ConfigEntry


class ConfigEntryRepository:
    """Repository for ConfigEntry CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_key(self, key: str) -> ConfigEntry | None:
        """Get a config entry by key."""
        query = select(ConfigEntry).where(ConfigEntry.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_value(self, key: str) -> str | None:
        """Get raw string value by key. Returns None if not found or not set."""
        entry = await self.get_by_key(key)
        if entry is None:
            return None
        return entry.value

    async def get_json_value(self, key: str) -> dict | list | None:
        """Get a JSON-parsed value by key. Returns None if not found or not set."""
        raw = await self.get_value(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def get_int_value(self, key: str) -> int | None:
        """Get an integer value by key. Returns None if not found or not set."""
        raw = await self.get_value(key)
        if raw is None:
            return None
        return int(raw)

    async def set_value(self, key: str, value: str) -> ConfigEntry | None:
        """Set the value for an existing config key. Returns None if key not found."""
        entry = await self.get_by_key(key)
        if entry is None:
            return None
        entry.value = value
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_all(self) -> list[ConfigEntry]:
        """List all config entries ordered by key."""
        query = select(ConfigEntry).order_by(ConfigEntry.key.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_required_unset(self) -> list[ConfigEntry]:
        """List required configs that have no value set."""
        query = (
            select(ConfigEntry)
            .where(
                ConfigEntry.is_required == True,  # noqa: E712
                ConfigEntry.value.is_(None),
            )
            .order_by(ConfigEntry.key.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
