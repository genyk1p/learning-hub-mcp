"""seed_bonus_fund

Revision ID: 77e62b90ce6e
Revises: 8a42871ab398
Create Date: 2026-02-16 19:31:17.595165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77e62b90ce6e'
down_revision: Union[str, Sequence[str], None] = '8a42871ab398'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bonus fund singleton row if table is empty."""
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM bonus_funds"))
    count = result.scalar()
    if count == 0:
        conn.execute(sa.text(
            "INSERT INTO bonus_funds (id, name, available_tasks, created_at, updated_at) "
            "VALUES (1, 'Bonus Fund', 0, datetime('now'), datetime('now'))"
        ))


def downgrade() -> None:
    """Remove seeded bonus fund row."""
    op.execute("DELETE FROM bonus_funds WHERE id = 1")
