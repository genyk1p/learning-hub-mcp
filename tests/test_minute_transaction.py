"""Tests for MinuteTransaction repository — immutable ledger."""

import pytest

from learning_hub.models.enums import TransactionType
from learning_hub.repositories.minute_transaction import MinuteTransactionRepository


pytestmark = pytest.mark.asyncio


# ---- balance tests ----


async def test_empty_balance(session):
    """Balance is 0 when no transactions exist."""
    repo = MinuteTransactionRepository(session)
    assert await repo.get_balance() == 0


async def test_balance_single_positive(session):
    """Balance reflects a single positive transaction."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=15, type=TransactionType.GRADE, description="Grade 1")
    assert await repo.get_balance() == 15


async def test_balance_single_negative(session):
    """Balance reflects a single negative transaction."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=-30, type=TransactionType.PLAYED, description="Played")
    assert await repo.get_balance() == -30


async def test_balance_multiple_transactions(session):
    """Balance is the sum of all transactions."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=15, type=TransactionType.GRADE, description="Grade 1")
    await repo.create(minutes=10, type=TransactionType.HOMEWORK, description="HW on time")
    await repo.create(minutes=-20, type=TransactionType.PLAYED, description="Played")
    await repo.create(minutes=5, type=TransactionType.AD_HOC, description="Bonus")
    # 15 + 10 - 20 + 5 = 10
    assert await repo.get_balance() == 10


async def test_balance_can_go_negative(session):
    """Balance can be negative (student owes time)."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=10, type=TransactionType.GRADE, description="Grade")
    await repo.create(minutes=-30, type=TransactionType.PLAYED, description="Played")
    assert await repo.get_balance() == -20


# ---- create tests ----


async def test_create_transaction(session):
    """Created transaction has correct fields."""
    repo = MinuteTransactionRepository(session)
    tx = await repo.create(
        minutes=15,
        type=TransactionType.GRADE,
        description="Math grade 1",
    )
    assert tx.id is not None
    assert tx.minutes == 15
    assert tx.type == TransactionType.GRADE.value
    assert tx.description == "Math grade 1"
    assert tx.grade_id is None
    assert tx.homework_id is None
    assert tx.bonus_task_id is None
    assert tx.created_at is not None


async def test_create_played_stores_negative(session):
    """PLAYED transactions store negative minutes."""
    repo = MinuteTransactionRepository(session)
    tx = await repo.create(minutes=-60, type=TransactionType.PLAYED, description="Gaming")
    assert tx.minutes == -60


# ---- list tests ----


async def test_list_all(session):
    """List returns all transactions newest first."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=10, type=TransactionType.GRADE, description="First")
    await repo.create(minutes=20, type=TransactionType.HOMEWORK, description="Second")

    txs = await repo.list()
    assert len(txs) == 2
    # Newest first
    assert txs[0].description == "Second"
    assert txs[1].description == "First"


async def test_list_filter_by_type(session):
    """List can filter by transaction type."""
    repo = MinuteTransactionRepository(session)
    await repo.create(minutes=10, type=TransactionType.GRADE, description="Grade")
    await repo.create(minutes=-30, type=TransactionType.PLAYED, description="Played")
    await repo.create(minutes=5, type=TransactionType.AD_HOC, description="Bonus")

    txs = await repo.list(type=TransactionType.PLAYED.value)
    assert len(txs) == 1
    assert txs[0].description == "Played"


# ---- idempotency lookup tests ----


async def test_get_by_homework_id(session):
    """Can find transaction by homework_id — returns None when no match."""
    repo = MinuteTransactionRepository(session)
    # No linked transactions exist
    assert await repo.get_by_homework_id(999) is None


async def test_get_by_bonus_task_id(session):
    """Can find transaction by bonus_task_id — returns None when no match."""
    repo = MinuteTransactionRepository(session)
    # No linked transactions exist
    assert await repo.get_by_bonus_task_id(999) is None
