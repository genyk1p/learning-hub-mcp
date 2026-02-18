"""Config tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.tools.tool_names import (
    TOOL_GET_CONFIG,
    TOOL_SET_CONFIG,
    TOOL_LIST_CONFIGS,
)
from learning_hub.utils import dt_to_str


class ConfigEntryResponse(BaseModel):
    """Config entry response schema."""
    key: str
    value: str | None
    description: str
    is_required: bool
    updated_at: str | None


def register_config_tools(mcp: FastMCP) -> None:
    """Register config management tools."""

    @mcp.tool(name=TOOL_GET_CONFIG, description="""Get a configuration value by key.

    Returns the config entry with its value, description, and metadata.

    Args:
        key: Config key (e.g. "GRADE_MINUTES_MAP", "TEMP_BOOK_DIR")

    Returns:
        Config entry or null if key not found
    """)
    async def get_config(key: str) -> ConfigEntryResponse | None:
        async with AsyncSessionLocal() as session:
            repo = ConfigEntryRepository(session)
            entry = await repo.get_by_key(key)
            if entry is None:
                return None
            return ConfigEntryResponse(
                key=entry.key,
                value=entry.value,
                description=entry.description,
                is_required=entry.is_required,
                updated_at=dt_to_str(entry.updated_at),
            )

    @mcp.tool(name=TOOL_SET_CONFIG, description="""Set a configuration value.

    Only updates existing config keys (created by migration).
    For JSON values (maps, lists), pass a valid JSON string.

    Args:
        key: Config key to update
        value: New value as string (use JSON for complex types)

    Returns:
        Updated config entry or null if key not found
    """)
    async def set_config(key: str, value: str) -> ConfigEntryResponse | None:
        async with AsyncSessionLocal() as session:
            repo = ConfigEntryRepository(session)
            entry = await repo.set_value(key, value)
            if entry is None:
                return None
            return ConfigEntryResponse(
                key=entry.key,
                value=entry.value,
                description=entry.description,
                is_required=entry.is_required,
                updated_at=dt_to_str(entry.updated_at),
            )

    @mcp.tool(name=TOOL_LIST_CONFIGS, description="""List all configuration entries.

    Returns all config keys with their values, descriptions, and metadata.
    Useful for seeing what's configured and what needs to be set.

    Returns:
        List of all config entries ordered by key
    """)
    async def list_configs() -> list[ConfigEntryResponse]:
        async with AsyncSessionLocal() as session:
            repo = ConfigEntryRepository(session)
            entries = await repo.list_all()
            return [
                ConfigEntryResponse(
                    key=e.key,
                    value=e.value,
                    description=e.description,
                    is_required=e.is_required,
                    updated_at=dt_to_str(e.updated_at),
                )
                for e in entries
            ]

