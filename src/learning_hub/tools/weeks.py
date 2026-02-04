"""Week tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.week import WeekRepository


class WeekResponse(BaseModel):
    """Week response schema."""
    week_key: str
    start_at: datetime | None
    end_at: datetime | None
    grade_minutes: int
    bonus_minutes: int
    penalty_minutes: int
    carryover_minutes: int
    actual_played_minutes: int
    total_minutes: int
    is_finalized: bool


def register_week_tools(mcp: FastMCP) -> None:
    """Register week-related tools."""

    @mcp.tool(description="""Create a new week period.

    Weeks run Saturday to Saturday. The week_key is the start date (YYYY-MM-DD).

    Args:
        week_key: Week identifier, typically the start date (e.g. "2026-02-01")
        start_at: Week start datetime, ISO format
        end_at: Week end datetime, ISO format

    Returns:
        Created week with all minute fields defaulting to 0
    """)
    async def create_week(
        week_key: str,
        start_at: str,
        end_at: str,
    ) -> WeekResponse:
        start_parsed = datetime.fromisoformat(start_at)
        end_parsed = datetime.fromisoformat(end_at)

        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)
            week = await repo.create(
                week_key=week_key,
                start_at=start_parsed,
                end_at=end_parsed,
            )
            return WeekResponse(
                week_key=week.week_key,
                start_at=week.start_at,
                end_at=week.end_at,
                grade_minutes=week.grade_minutes,
                bonus_minutes=week.bonus_minutes,
                penalty_minutes=week.penalty_minutes,
                carryover_minutes=week.carryover_minutes,
                actual_played_minutes=week.actual_played_minutes,
                total_minutes=week.total_minutes,
                is_finalized=week.is_finalized,
            )

    @mcp.tool(description="""Get a week by key or get current week.

    Args:
        week_key: Week key to fetch (e.g. "2026-02-01"). If not provided, returns current week.

    Returns:
        Week data or null if not found
    """)
    async def get_week(week_key: str | None = None) -> WeekResponse | None:
        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)

            if week_key:
                week = await repo.get_by_key(week_key)
            else:
                week = await repo.get_current(datetime.now())

            if week is None:
                return None

            return WeekResponse(
                week_key=week.week_key,
                start_at=week.start_at,
                end_at=week.end_at,
                grade_minutes=week.grade_minutes,
                bonus_minutes=week.bonus_minutes,
                penalty_minutes=week.penalty_minutes,
                carryover_minutes=week.carryover_minutes,
                actual_played_minutes=week.actual_played_minutes,
                total_minutes=week.total_minutes,
                is_finalized=week.is_finalized,
            )

    @mcp.tool(description="""Update week minutes.

    Args:
        week_key: Week key to update
        grade_minutes: Minutes earned from grades (optional)
        bonus_minutes: Minutes earned from bonus tasks (optional)
        penalty_minutes: Minutes lost as penalty (optional)
        carryover_minutes: Minutes carried over from previous week (optional)
        actual_played_minutes: Minutes actually played this week (optional)
        total_minutes: Calculated total available minutes (optional)

    Returns:
        Updated week or null if not found
    """)
    async def update_week(
        week_key: str,
        grade_minutes: int | None = None,
        bonus_minutes: int | None = None,
        penalty_minutes: int | None = None,
        carryover_minutes: int | None = None,
        actual_played_minutes: int | None = None,
        total_minutes: int | None = None,
    ) -> WeekResponse | None:
        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)
            week = await repo.update(
                week_key=week_key,
                grade_minutes=grade_minutes,
                bonus_minutes=bonus_minutes,
                penalty_minutes=penalty_minutes,
                carryover_minutes=carryover_minutes,
                actual_played_minutes=actual_played_minutes,
                total_minutes=total_minutes,
            )
            if week is None:
                return None

            return WeekResponse(
                week_key=week.week_key,
                start_at=week.start_at,
                end_at=week.end_at,
                grade_minutes=week.grade_minutes,
                bonus_minutes=week.bonus_minutes,
                penalty_minutes=week.penalty_minutes,
                carryover_minutes=week.carryover_minutes,
                actual_played_minutes=week.actual_played_minutes,
                total_minutes=week.total_minutes,
                is_finalized=week.is_finalized,
            )

    @mcp.tool(description="""Finalize a week.

    Once finalized, the week's data should not be modified.
    Carryover minutes are calculated for the next week.

    Args:
        week_key: Week key to finalize

    Returns:
        Finalized week or null if not found
    """)
    async def finalize_week(week_key: str) -> WeekResponse | None:
        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)
            week = await repo.finalize(week_key)
            if week is None:
                return None

            return WeekResponse(
                week_key=week.week_key,
                start_at=week.start_at,
                end_at=week.end_at,
                grade_minutes=week.grade_minutes,
                bonus_minutes=week.bonus_minutes,
                penalty_minutes=week.penalty_minutes,
                carryover_minutes=week.carryover_minutes,
                actual_played_minutes=week.actual_played_minutes,
                total_minutes=week.total_minutes,
                is_finalized=week.is_finalized,
            )

