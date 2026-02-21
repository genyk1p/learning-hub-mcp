"""add_setup_completed_config

Revision ID: ee793270e1d2
Revises: a5ceb6f55dea
Create Date: 2026-02-21 22:31:04.290365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee793270e1d2'
down_revision: Union[str, Sequence[str], None] = 'a5ceb6f55dea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed SETUP_COMPLETED config entry (default: false)."""
    conn = op.get_bind()
    conn.execute(sa.text(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) "
        "VALUES (:key, :value, :desc, :req, datetime('now'), datetime('now'))"
    ), {
        "key": "SETUP_COMPLETED",
        "value": "false",
        "desc": "Whether initial setup has been completed",
        "req": False,
    })


def downgrade() -> None:
    """Remove SETUP_COMPLETED config entry."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM configs WHERE key = 'SETUP_COMPLETED'"))
