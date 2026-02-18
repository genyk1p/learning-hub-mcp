"""BonusFund tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.bonus_fund import BonusFundRepository
from learning_hub.tools.tool_names import (
    TOOL_GET_BONUS_FUND,
    TOOL_ADD_TASKS_TO_FUND,
)
from learning_hub.utils import dt_to_str


class BonusFundResponse(BaseModel):
    """BonusFund response schema."""
    id: int
    name: str
    available_tasks: int
    created_at: str | None
    updated_at: str | None


def register_bonus_fund_tools(mcp: FastMCP) -> None:
    """Register bonus fund related tools."""

    @mcp.tool(name=TOOL_GET_BONUS_FUND, description="""Get the bonus fund.

    Shows the fund name and how many bonus task slots are available.

    Returns:
        Bonus fund or null if not found
    """)
    async def get_bonus_fund() -> BonusFundResponse | None:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            fund = await repo.get()
            if fund is None:
                return None
            return BonusFundResponse(
                id=fund.id,
                name=fund.name,
                available_tasks=fund.available_tasks,
                created_at=dt_to_str(fund.created_at),
                updated_at=dt_to_str(fund.updated_at),
            )

    @mcp.tool(name=TOOL_ADD_TASKS_TO_FUND, description="""Add task slots to the bonus fund.

    Use this to increase the number of bonus tasks that can be assigned.
    Slots are deducted when bonus tasks are completed.

    Args:
        count: Number of task slots to add

    Returns:
        Updated fund with before/after balance, or null if not found
    """)
    async def add_tasks_to_fund(count: int) -> dict | None:
        async with AsyncSessionLocal() as session:
            repo = BonusFundRepository(session)
            fund, available_before = await repo.add_tasks(count=count)
            if fund is None:
                return None
            return {
                "fund": BonusFundResponse(
                    id=fund.id,
                    name=fund.name,
                    available_tasks=fund.available_tasks,
                    created_at=dt_to_str(fund.created_at),
                    updated_at=dt_to_str(fund.updated_at),
                ).model_dump(),
                "tasks_added": count,
                "available_before": available_before,
                "available_after": fund.available_tasks,
            }
