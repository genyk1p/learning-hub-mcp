"""Week tools for MCP server."""

from collections import Counter
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.bonus import BonusRepository
from learning_hub.repositories.bonus_fund import BonusFundRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.week import WeekRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_WEEK,
    TOOL_GET_WEEK,
    TOOL_UPDATE_WEEK,
    TOOL_FINALIZE_WEEK,
    TOOL_CALCULATE_WEEKLY_MINUTES,
    TOOL_GET_GRADE_TO_MINUTES_MAP,
)
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.tools.config_vars import (
    CFG_BONUS_FUND_WEEKLY_TOPUP,
    CFG_GRADE_MINUTES_MAP,
    CFG_HOMEWORK_BONUS_MINUTES_ONTIME,
    CFG_HOMEWORK_BONUS_MINUTES_OVERDUE,
)
from learning_hub.utils import dt_to_str

# Fallback if config DB is empty
_DEFAULT_GRADE_MINUTES_MAP = {1: 15, 2: 10, 3: 0, 4: -20, 5: -25}


class WeekResponse(BaseModel):
    """Week response schema."""
    week_key: str
    start_at: str | None
    end_at: str | None
    grade_minutes: int
    homework_bonus_minutes: int
    penalty_minutes: int
    carryover_out_minutes: int
    actual_played_minutes: int
    total_minutes: int
    is_finalized: bool


def _week_response(week) -> WeekResponse:
    """Build WeekResponse from a Week model instance."""
    return WeekResponse(
        week_key=week.week_key,
        start_at=dt_to_str(week.start_at),
        end_at=dt_to_str(week.end_at),
        grade_minutes=week.grade_minutes,
        homework_bonus_minutes=week.homework_bonus_minutes,
        penalty_minutes=week.penalty_minutes,
        carryover_out_minutes=week.carryover_out_minutes,
        actual_played_minutes=week.actual_played_minutes,
        total_minutes=week.total_minutes,
        is_finalized=week.is_finalized,
    )


class GradeBreakdown(BaseModel):
    """Breakdown of one grade value in the weekly calculation."""
    grade_value: int
    count: int
    minutes: int


class WeeklyCalcResult(BaseModel):
    """Result of calculate_weekly_minutes."""
    status: str
    new_week_key: str
    prev_week_key: str
    # Populated only when status == "ok"
    carry_from_prev: int | None = None
    grade_minutes: int | None = None
    homework_bonus_minutes: int | None = None
    penalty_minutes: int | None = None
    total_minutes: int | None = None
    grades_processed: int | None = None
    bonuses_processed: int | None = None
    bonus_fund_topup: int | None = None
    grades_breakdown: list[GradeBreakdown] | None = None
    week: WeekResponse | None = None
    # Human-readable message (always present)
    message: str = ""


def register_week_tools(mcp: FastMCP) -> None:
    """Register week-related tools."""

    @mcp.tool(name=TOOL_CREATE_WEEK, description="""Create a new week period.

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
            return _week_response(week)

    @mcp.tool(name=TOOL_GET_WEEK, description="""Get a week by key or get current week.

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

            return _week_response(week)

    @mcp.tool(name=TOOL_UPDATE_WEEK, description="""Update week minutes.

    Args:
        week_key: Week key to update
        grade_minutes: Minutes earned from grades (optional)
        penalty_minutes: Minutes lost as penalty (optional)
        carryover_out_minutes: Minutes carried over from previous week (optional)
        actual_played_minutes: Minutes actually played this week (optional)
        total_minutes: Calculated total available minutes (optional)

    Returns:
        Updated week or null if not found
    """)
    async def update_week(
        week_key: str,
        grade_minutes: int | None = None,
        penalty_minutes: int | None = None,
        carryover_out_minutes: int | None = None,
        actual_played_minutes: int | None = None,
        total_minutes: int | None = None,
    ) -> WeekResponse | None:
        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)
            week = await repo.update(
                week_key=week_key,
                grade_minutes=grade_minutes,
                penalty_minutes=penalty_minutes,
                carryover_out_minutes=carryover_out_minutes,
                actual_played_minutes=actual_played_minutes,
                total_minutes=total_minutes,
            )
            if week is None:
                return None

            return _week_response(week)

    @mcp.tool(name=TOOL_FINALIZE_WEEK, description="""Finalize a week.

    Saves actual played minutes, calculates carryover (total_minutes - actual_played_minutes),
    and marks the week as finalized. Once finalized, the week should not be modified.

    Args:
        week_key: Week key to finalize
        actual_played_minutes: Minutes actually played this week

    Returns:
        Finalized week or null if not found
    """)
    async def finalize_week(week_key: str, actual_played_minutes: int) -> WeekResponse | None:
        async with AsyncSessionLocal() as session:
            repo = WeekRepository(session)
            week = await repo.finalize(week_key, actual_played_minutes)
            if week is None:
                return None

            return _week_response(week)

    @mcp.tool(name=TOOL_CALCULATE_WEEKLY_MINUTES, description=f"""Calculate weekly game minutes.

    Performs the full weekly calculation:
    1. Validates that previous week is finalized
    2. Creates new week record (if missing)
    3. Calculates grade_minutes from unrewarded grades (conversion from {CFG_GRADE_MINUTES_MAP} config)
    4. Calculates homework_bonus_minutes from unrewarded homework bonuses ({CFG_HOMEWORK_BONUS_MINUTES_ONTIME} / {CFG_HOMEWORK_BONUS_MINUTES_OVERDUE} configs)
    5. Computes total = carryover + grade_minutes + homework_bonus_minutes - penalties
    6. Marks all processed grades and bonuses as rewarded
    7. Tops up bonus fund ({CFG_BONUS_FUND_WEEKLY_TOPUP} config)

    Args:
        new_week_key: Saturday date for the new week (YYYY-MM-DD)
        bonus_fund_topup: Override bonus task slots to add (default from {CFG_BONUS_FUND_WEEKLY_TOPUP} config)

    Returns:
        Detailed breakdown, or status="prev_week_not_finalized" if previous week is not closed
    """)
    async def calculate_weekly_minutes(
        new_week_key: str,
        bonus_fund_topup: int | None = None,
    ) -> WeeklyCalcResult:
        new_week_date = datetime.fromisoformat(new_week_key).date()
        prev_week_date = new_week_date - timedelta(days=7)
        prev_week_key = prev_week_date.isoformat()

        async with AsyncSessionLocal() as session:
            week_repo = WeekRepository(session)
            grade_repo = GradeRepository(session)
            bonus_repo = BonusRepository(session)
            fund_repo = BonusFundRepository(session)
            config_repo = ConfigEntryRepository(session)

            # Read config values
            grade_map_raw = await config_repo.get_json_value(CFG_GRADE_MINUTES_MAP)
            grade_minutes_map = (
                {int(k): v for k, v in grade_map_raw.items()}
                if isinstance(grade_map_raw, dict)
                else _DEFAULT_GRADE_MINUTES_MAP
            )

            if bonus_fund_topup is None:
                bonus_fund_topup = (
                    await config_repo.get_int_value(CFG_BONUS_FUND_WEEKLY_TOPUP) or 15
                )

            # Step 1: check prev week is finalized
            prev_week = await week_repo.get_by_key(prev_week_key)
            if prev_week is None or not prev_week.is_finalized:
                return WeeklyCalcResult(
                    status="prev_week_not_finalized",
                    new_week_key=new_week_key,
                    prev_week_key=prev_week_key,
                    message=(
                        f"Previous week {prev_week_key} is not finalized. "
                        "Provide actual_played_minutes via finalize_week first."
                    ),
                )

            carry = prev_week.carryover_out_minutes

            # Step 2: get or create new week
            new_week = await week_repo.get_by_key(new_week_key)
            if new_week is not None:
                return WeeklyCalcResult(
                    status="already_calculated",
                    new_week_key=new_week_key,
                    prev_week_key=prev_week_key,
                    week=_week_response(new_week),
                    message=f"Week {new_week_key} already calculated.",
                )

            start_at = prev_week.end_at
            end_at = start_at + timedelta(days=7)
            new_week = await week_repo.create(
                week_key=new_week_key,
                start_at=start_at,
                end_at=end_at,
            )

            penalty_minutes = new_week.penalty_minutes

            # Step 3: get unrewarded grades for the period
            grades = await grade_repo.list(
                date_from=prev_week.start_at,
                date_to=prev_week.end_at,
                rewarded=False,
            )

            # Step 4: calculate grade_minutes
            grade_minutes = 0
            grade_counter: Counter[int] = Counter()
            for grade in grades:
                gv = grade.grade_value.value
                minutes = grade_minutes_map.get(gv, 0)
                grade_minutes += minutes
                grade_counter[gv] += 1

            # Step 5: get unrewarded homework bonuses
            bonuses = await bonus_repo.list_unrewarded()
            homework_bonus_minutes = sum(b.minutes for b in bonuses)

            # Step 6: calculate total
            total_minutes = carry + grade_minutes + homework_bonus_minutes - penalty_minutes

            # Step 7: update new week record
            new_week = await week_repo.update(
                week_key=new_week_key,
                grade_minutes=grade_minutes,
                homework_bonus_minutes=homework_bonus_minutes,
                total_minutes=total_minutes,
            )

            # Step 8: mark grades as rewarded (batch)
            grade_ids = [g.id for g in grades]
            grades_marked = await grade_repo.mark_rewarded(grade_ids)

            # Step 9: mark bonuses as rewarded
            bonuses_marked = await bonus_repo.mark_all_rewarded()

            # Step 10: top up bonus fund
            if bonus_fund_topup > 0:
                await fund_repo.add_tasks(bonus_fund_topup)

            # Build grades breakdown
            grades_breakdown = [
                GradeBreakdown(
                    grade_value=gv,
                    count=count,
                    minutes=grade_minutes_map.get(gv, 0) * count,
                )
                for gv, count in sorted(grade_counter.items())
            ]

            return WeeklyCalcResult(
                status="ok",
                new_week_key=new_week_key,
                prev_week_key=prev_week_key,
                carry_from_prev=carry,
                grade_minutes=grade_minutes,
                homework_bonus_minutes=homework_bonus_minutes,
                penalty_minutes=penalty_minutes,
                total_minutes=total_minutes,
                grades_processed=grades_marked,
                bonuses_processed=bonuses_marked,
                bonus_fund_topup=bonus_fund_topup,
                grades_breakdown=grades_breakdown,
                week=_week_response(new_week),
                message=(
                    f"Week {new_week_key}: "
                    f"grades={grade_minutes}, homework={homework_bonus_minutes}, "
                    f"carry={carry}, penalty={penalty_minutes}, "
                    f"total={total_minutes} min."
                ),
            )

    @mcp.tool(name=TOOL_GET_GRADE_TO_MINUTES_MAP, description=f"""Get the grade-to-minutes conversion table.

    Returns the current {CFG_GRADE_MINUTES_MAP} from config.
    Uses 5-point European grading scale (1 = best, 5 = worst).

    Returns:
        Mapping of grade values to minutes
    """)
    async def get_grade_to_minutes_map() -> dict[str, int]:
        async with AsyncSessionLocal() as session:
            config_repo = ConfigEntryRepository(session)
            raw = await config_repo.get_json_value(CFG_GRADE_MINUTES_MAP)
            if isinstance(raw, dict):
                return {str(k): v for k, v in raw.items()}
            return {str(k): v for k, v in _DEFAULT_GRADE_MINUTES_MAP.items()}
