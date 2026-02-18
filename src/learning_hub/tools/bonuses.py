"""Bonus tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_BONUS,
    TOOL_DELETE_BONUS,
    TOOL_LIST_UNREWARDED_BONUSES,
    TOOL_MARK_BONUSES_REWARDED,
)
from learning_hub.utils import dt_to_str


class BonusResponse(BaseModel):
    """Bonus response schema."""
    id: int
    homework_id: int
    minutes: int
    rewarded: bool
    created_at: str | None


def register_bonus_tools(mcp: FastMCP) -> None:
    """Register bonus-related tools."""

    @mcp.tool(name=TOOL_CREATE_BONUS, description="""Create a new bonus minutes record.

    Bonus minutes can be positive (reward) or negative (penalty).
    Linked to a homework (one bonus per homework).

    Args:
        homework_id: ID of the related homework
        minutes: Number of bonus minutes (positive=reward, negative=penalty)

    Returns:
        Created bonus
    """)
    async def create_bonus(
        homework_id: int,
        minutes: int,
    ) -> BonusResponse:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            bonus = await repo.create(
                homework_id=homework_id,
                minutes=minutes,
            )
            return BonusResponse(
                id=bonus.id,
                homework_id=bonus.homework_id,
                minutes=bonus.minutes,
                rewarded=bonus.rewarded,
                created_at=dt_to_str(bonus.created_at),
            )

    @mcp.tool(name=TOOL_DELETE_BONUS, description="""Delete a bonus record.

    Args:
        bonus_id: ID of the bonus to delete

    Returns:
        True if deleted, False if not found
    """)
    async def delete_bonus(bonus_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            return await repo.delete(bonus_id)

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
                    rewarded=b.rewarded,
                    created_at=dt_to_str(b.created_at),
                )
                for b in bonuses
            ]

    @mcp.tool(name=TOOL_MARK_BONUSES_REWARDED, description="""Mark all unrewarded bonuses as rewarded.

    Sets rewarded=True for all bonuses where rewarded=False.
    Use this during weekly game minutes calculation.

    Returns:
        Count of bonuses marked as rewarded
    """)
    async def mark_bonuses_rewarded() -> int:
        async with AsyncSessionLocal() as session:
            repo = BonusRepository(session)
            return await repo.mark_all_rewarded()
