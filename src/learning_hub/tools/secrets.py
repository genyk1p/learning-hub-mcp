"""Secret tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.secret import SecretRepository
from learning_hub.tools.tool_names import (
    TOOL_SET_SECRET,
    TOOL_LIST_SECRETS,
)
from learning_hub.utils import dt_to_str


class SecretEntryResponse(BaseModel):
    """Secret entry response schema (value is never exposed)."""
    key: str
    description: str
    is_set: bool
    updated_at: str | None


def register_secret_tools(mcp: FastMCP) -> None:
    """Register secret management tools."""

    @mcp.tool(name=TOOL_SET_SECRET, description="""Set a secret value.

    Only updates existing secret keys (created by migration).
    Use this during initial setup to configure credentials.

    Args:
        key: Secret key to update (e.g. "EDUPAGE_PASSWORD")
        value: Secret value to store

    Returns:
        Confirmation with key and description (value is never returned)
        or null if key not found
    """)
    async def set_secret(key: str, value: str) -> SecretEntryResponse | str:
        value = value.strip()
        if not value:
            return "Secret value cannot be empty."
        async with AsyncSessionLocal() as session:
            repo = SecretRepository(session)
            entry = await repo.set_value(key, value)
            if entry is None:
                return (
                    f"Secret key '{key}' not found. "
                    "Only pre-defined keys (from migrations) can be set. "
                    "Use list_secrets to see available keys."
                )
            return SecretEntryResponse(
                key=entry.key,
                description=entry.description,
                is_set=True,
                updated_at=dt_to_str(entry.updated_at),
            )

    @mcp.tool(name=TOOL_LIST_SECRETS, description="""List all secret entries.

    Returns all secret keys with their descriptions and whether they are set.
    Secret values are never returned — only metadata.

    Returns:
        List of all secret entries ordered by key
    """)
    async def list_secrets() -> list[SecretEntryResponse]:
        async with AsyncSessionLocal() as session:
            repo = SecretRepository(session)
            entries = await repo.list_all()
            return [
                SecretEntryResponse(
                    key=e.key,
                    description=e.description,
                    is_set=e.value is not None,
                    updated_at=dt_to_str(e.updated_at),
                )
                for e in entries
            ]
