"""seed_pronote_secrets

Revision ID: 6069fec62a0e
Revises: 36e84c5b2e81
Create Date: 2026-02-22 15:26:56.522558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6069fec62a0e'
down_revision: Union[str, Sequence[str], None] = '36e84c5b2e81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PRONOTE_SECRETS = [
    ("PRONOTE_URL", "PRONOTE instance URL (e.g. https://xxx.index-education.net/pronote/eleve.html)"),
    ("PRONOTE_USERNAME", "PRONOTE account username"),
    ("PRONOTE_PASSWORD", "PRONOTE account password"),
]


def upgrade() -> None:
    """Seed PRONOTE secret entries with NULL values."""
    conn = op.get_bind()
    for key, description in PRONOTE_SECRETS:
        conn.execute(sa.text(
            "INSERT INTO secrets (key, value, description, "
            "created_at, updated_at) "
            "VALUES (:key, NULL, :desc, datetime('now'), datetime('now'))"
        ), {"key": key, "desc": description})


def downgrade() -> None:
    """Remove PRONOTE secret entries."""
    conn = op.get_bind()
    for key, _ in PRONOTE_SECRETS:
        conn.execute(sa.text(
            "DELETE FROM secrets WHERE key = :key"
        ), {"key": key})
