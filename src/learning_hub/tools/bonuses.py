"""Bonus tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_BONUS,
    TOOL_DELETE_BONUS,
    TOOL_LIST_UNREWARDED_BONUSES,
)
from learning_hub.utils import dt_to_str


class BonusResponse(BaseModel):
    """Bonus response schema."""
    id: int
    homework_id: int | None
    minutes: int
    reason: str | None
    rewarded: bool
    created_at: str | None


def register_bonus_tools(mcp: FastMCP) -> None:
    """Register bonus-related tools."""

    @mcp.tool(name=TOOL_CREATE_BONUS, description="""Create a new bonus minutes record.

    Bonus minutes can be positive (reward) or negative (penalty).
    Two modes:
    - Homework-linked: provide homework_id (one bonus per homework).
    - Ad-hoc: no homework_id, provide reason (e.g. "good behavior", "penalty for lying").

    Args:
        minutes: Number of bonus minutes (positive=reward, negative=penalty)
        homework_id: ID of the related homework (optional, for homework bonuses)
        reason: Why this bonus was given (optional, for ad-hoc bonuses)

    Returns:
        Created bonus, or error dict if validation fails
    """)
    async def create_bonus(
        minutes: int,
        homework_id: int | None = None,
        reason: str | None = None,
    ) -> BonusResponse | dict:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            try:
                bonus = await repo.create(
                    minutes=minutes,
                    homework_id=homework_id,
                    reason=reason,
                )
            except ValueError as e:
                return {"error": str(e)}
            return BonusResponse(
                id=bonus.id,
                homework_id=bonus.homework_id,
                minutes=bonus.minutes,
                reason=bonus.reason,
                rewarded=bonus.rewarded,
                created_at=dt_to_str(bonus.created_at),
            )

    @mcp.tool(name=TOOL_DELETE_BONUS, description="""Delete a bonus record.

    Only unrewarded bonuses can be deleted. Rewarded bonuses (already counted
    in weekly calculation) are protected from deletion.

    Args:
        bonus_id: ID of the bonus to delete

    Returns:
        Success status, or error dict if not found or already rewarded
    """)
    async def delete_bonus(bonus_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            success, error = await repo.delete(bonus_id)
            if error is not None:
                return {"error": error}
            return {"deleted": success}

    @mcp.tool(name=TOOL_LIST_UNREWARDED_BONUSES, description="""List bonus records not yet counted in weekly calculation.

    Returns all bonuses where rewarded=False, ordered by created_at descending.

    Returns:
        List of unrewarded bonuses
    """)
    async def list_unrewarded_bonuses() -> list[BonusResponse]:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            bonuses = await repo.list_unrewarded()
            return [
                BonusResponse(
                    id=b.id,
                    homework_id=b.homework_id,
                    minutes=b.minutes,
                    reason=b.reason,
                    rewarded=b.rewarded,
                    created_at=dt_to_str(b.created_at),
                )
                for b in bonuses
            ]
