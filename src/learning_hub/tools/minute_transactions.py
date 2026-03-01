"""Minute transaction tools for MCP server."""

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import TransactionType
from learning_hub.repositories.minute_transaction import MinuteTransactionRepository
from learning_hub.tools.tool_names import (
    TOOL_ADD_PLAYED_MINUTES,
    TOOL_CREATE_AD_HOC_TRANSACTION,
    TOOL_GET_BALANCE,
    TOOL_LIST_TRANSACTIONS,
)
from learning_hub.utils import dt_to_str


class TransactionResponse(BaseModel):
    """Minute transaction response schema."""
    id: int
    minutes: int
    type: str
    description: str | None
    grade_id: int | None
    homework_id: int | None
    bonus_task_id: int | None
    created_at: str | None


def _tx_response(tx) -> TransactionResponse:
    """Build TransactionResponse from a MinuteTransaction instance."""
    return TransactionResponse(
        id=tx.id,
        minutes=tx.minutes,
        type=tx.type,
        description=tx.description,
        grade_id=tx.grade_id,
        homework_id=tx.homework_id,
        bonus_task_id=tx.bonus_task_id,
        created_at=dt_to_str(tx.created_at),
    )


def register_minute_transaction_tools(mcp: FastMCP) -> None:
    """Register minute transaction tools."""

    @mcp.tool(name=TOOL_GET_BALANCE, description="""Get current game minutes balance.

    Returns the sum of all minute transactions (earned minus spent).
    Positive = student has available game time.
    Negative = student owes time (overspent).

    Returns:
        Current balance in minutes
    """)
    async def get_balance() -> dict:
        async with AsyncSessionLocal() as session:
            repo = MinuteTransactionRepository(session)
            balance = await repo.get_balance()
            return {"balance": balance}

    @mcp.tool(name=TOOL_ADD_PLAYED_MINUTES, description="""Record that the student played.

    Creates a negative PLAYED transaction that reduces the balance.

    Args:
        minutes: How many minutes the student played (positive number)
        description: Optional note (e.g. "Saturday gaming session")

    Returns:
        Created transaction and new balance
    """)
    async def add_played_minutes(
        minutes: int,
        description: str | None = None,
    ) -> dict:
        if minutes <= 0:
            return {"error": "minutes must be a positive number"}

        async with AsyncSessionLocal() as session:
            repo = MinuteTransactionRepository(session)
            tx = await repo.create(
                minutes=-minutes,
                type=TransactionType.PLAYED,
                description=description or f"Played {minutes} min",
            )
            balance = await repo.get_balance()
            return {
                "transaction": _tx_response(tx).model_dump(),
                "balance": balance,
            }

    @mcp.tool(name=TOOL_CREATE_AD_HOC_TRANSACTION, description="""Create a manual bonus or penalty.

    Use this for one-off adjustments not tied to a grade or homework.
    Positive minutes = bonus (e.g. good behavior).
    Negative minutes = penalty (e.g. rule violation).

    Args:
        minutes: Minutes to add (positive) or subtract (negative)
        description: Reason for the adjustment (required)

    Returns:
        Created transaction and new balance
    """)
    async def create_ad_hoc_transaction(
        minutes: int,
        description: str,
    ) -> dict:
        if not description or not description.strip():
            return {"error": "description is required for ad-hoc transactions"}

        async with AsyncSessionLocal() as session:
            repo = MinuteTransactionRepository(session)
            tx = await repo.create(
                minutes=minutes,
                type=TransactionType.AD_HOC,
                description=description.strip(),
            )
            balance = await repo.get_balance()
            return {
                "transaction": _tx_response(tx).model_dump(),
                "balance": balance,
            }

    @mcp.tool(name=TOOL_LIST_TRANSACTIONS, description="""List minute transactions.

    Args:
        date_from: Filter from this date, ISO format (optional)
        date_to: Filter until this date, ISO format (optional)
        type: Filter by type: grade, homework, bonus_task, ad_hoc, played (optional)

    Returns:
        List of transactions, newest first
    """)
    async def list_transactions(
        date_from: str | None = None,
        date_to: str | None = None,
        type: str | None = None,
    ) -> list[TransactionResponse]:
        date_from_parsed = datetime.fromisoformat(date_from) if date_from else None
        date_to_parsed = datetime.fromisoformat(date_to) if date_to else None

        async with AsyncSessionLocal() as session:
            repo = MinuteTransactionRepository(session)
            transactions = await repo.list(
                date_from=date_from_parsed,
                date_to=date_to_parsed,
                type=type,
            )
            return [_tx_response(tx) for tx in transactions]
