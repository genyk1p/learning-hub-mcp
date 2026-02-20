"""Add source field to grades

Revision ID: b92c3c323049
Revises: a1b2c3d4e5f6
Create Date: 2026-02-20 17:47:57.643527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b92c3c323049'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column with server_default for existing rows
    op.add_column(
        'grades',
        sa.Column('source', sa.String(length=10), nullable=False, server_default='manual'),
    )

    # Set existing EduPage grades to 'auto'
    op.execute("UPDATE grades SET source = 'auto' WHERE edupage_id IS NOT NULL")

    # Remove server_default (new rows get default from Python model)
    with op.batch_alter_table('grades') as batch_op:
        batch_op.alter_column('source', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('grades', 'source')
