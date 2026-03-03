"""Add is_favorite column to subjects table.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("subjects") as batch_op:
        batch_op.add_column(
            sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("0"))
        )


def downgrade() -> None:
    with op.batch_alter_table("subjects") as batch_op:
        batch_op.drop_column("is_favorite")
