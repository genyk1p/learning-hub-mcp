"""add_family_language_config

Revision ID: 8cf801318955
Revises: efc35e94c595
Create Date: 2026-02-17 21:23:32.755882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cf801318955'
down_revision: Union[str, Sequence[str], None] = 'efc35e94c595'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed FAMILY_LANGUAGE config entry."""
    conn = op.get_bind()
    conn.execute(sa.text(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) "
        "VALUES (:key, NULL, :desc, :req, datetime('now'), datetime('now'))"
    ), {
        "key": "FAMILY_LANGUAGE",
        "desc": "Language for communication with the family (e.g. русский)",
        "req": True,
    })


def downgrade() -> None:
    """Remove FAMILY_LANGUAGE config entry."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM configs WHERE key = 'FAMILY_LANGUAGE'"))
