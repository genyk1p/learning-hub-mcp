"""Database connection and session management."""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from learning_hub.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Log SQL queries (disable in production)
)


# Enable SQLite foreign key enforcement on every connection
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session
