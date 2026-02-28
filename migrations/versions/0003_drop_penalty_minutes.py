"""Drop penalty_minutes column from weeks table.

The field was intended for future penalty logic but was never implemented.
Penalties are handled via the bonuses table (negative minutes).

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "0003"
down_revision = "68fe7e62f88b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("weeks", "penalty_minutes")


def downgrade() -> None:
    op.add_column(
        "weeks",
        sa.Column("penalty_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
