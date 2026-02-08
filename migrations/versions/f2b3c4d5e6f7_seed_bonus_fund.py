"""Seed bonus fund singleton row

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-02-08 20:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bonus fund row if table is empty."""
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
