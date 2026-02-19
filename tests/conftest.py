"""Shared fixtures for tests."""

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from learning_hub.models.base import Base


@pytest_asyncio.fixture
async def session():
    """Async session with in-memory SQLite database.

    Creates all tables before test, drops after.
    """
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # Enable FK enforcement for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import all models so Base.metadata knows about them
    from learning_hub.models.family_member import FamilyMember  # noqa: F401
    from learning_hub.models.gateway import Gateway  # noqa: F401
    from learning_hub.models.school import School  # noqa: F401
    from learning_hub.models.subject import Subject  # noqa: F401
    from learning_hub.models.subject_topic import SubjectTopic  # noqa: F401
    from learning_hub.models.grade import Grade  # noqa: F401
    from learning_hub.models.bonus_task import BonusTask  # noqa: F401
    from learning_hub.models.bonus_fund import BonusFund  # noqa: F401
    from learning_hub.models.homework import Homework  # noqa: F401
    from learning_hub.models.week import Week  # noqa: F401
    from learning_hub.models.book import Book  # noqa: F401
    from learning_hub.models.topic_review import TopicReview  # noqa: F401
    from learning_hub.models.bonus import Bonus  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
