"""BonusFund tools for MCP server."""

from datetime import datetime
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.bonus_fund import BonusFundRepository


class BonusFundResponse(BaseModel):
    """BonusFund response schema."""
    id: int
    name: str
    minutes: int
    created_at: datetime
    updated_at: datetime


def register_bonus_fund_tools(mcp: FastMCP) -> None:
    """Register bonus fund related tools."""

    @mcp.tool(description="""Create a new bonus fund.

    Bonus funds store minutes that can be awarded for extra tasks.
    The agent should create a creative name for each fund.

    Args:
        name: Creative name for the fund (agent invents this)
        minutes: Initial minutes in the fund (default 0)

    Returns:
        Created bonus fund
    """)
    async def create_bonus_fund(
        name: str,
        minutes: int = 0,
    ) -> BonusFundResponse:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            fund = await repo.create(name=name, minutes=minutes)
            return BonusFundResponse(
                id=fund.id,
                name=fund.name,
                minutes=fund.minutes,
                created_at=fund.created_at,
                updated_at=fund.updated_at,
            )

    @mcp.tool(description="""Add minutes to a bonus fund.

    Use this to deposit minutes into a fund.
    Minutes will be automatically deducted when bonus tasks are completed.

    Args:
        fund_id: ID of the fund
        minutes: Minutes to add to the fund balance

    Returns:
        Updated fund with before/after balance, or null if not found
    """)
    async def add_minutes_to_fund(
        fund_id: int,
        minutes: int,
    ) -> dict | None:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            fund, minutes_before = await repo.add_minutes(fund_id=fund_id, minutes=minutes)
            if fund is None:
                return None
            return {
                "fund": BonusFundResponse(
                    id=fund.id,
                    name=fund.name,
                    minutes=fund.minutes,
                    created_at=fund.created_at,
                    updated_at=fund.updated_at,
                ).model_dump(),
                "minutes_added": minutes,
                "minutes_before": minutes_before,
                "minutes_after": fund.minutes,
            }

    @mcp.tool(description="""Rename a bonus fund.

    Args:
        fund_id: ID of the fund to rename
        name: New name for the fund

    Returns:
        Updated fund or null if not found
    """)
    async def rename_bonus_fund(
        fund_id: int,
        name: str,
    ) -> BonusFundResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            fund = await repo.rename(fund_id=fund_id, name=name)
            if fund is None:
                return None
            return BonusFundResponse(
                id=fund.id,
                name=fund.name,
                minutes=fund.minutes,
                created_at=fund.created_at,
                updated_at=fund.updated_at,
            )

    @mcp.tool(description="""List all bonus funds.

    Shows all funds with their names and available minutes.

    Returns:
        List of bonus funds
    """)
    async def list_bonus_funds() -> list[BonusFundResponse]:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            funds = await repo.list()
            return [
                BonusFundResponse(
                    id=f.id,
                    name=f.name,
                    minutes=f.minutes,
                    created_at=f.created_at,
                    updated_at=f.updated_at,
                )
                for f in funds
            ]
