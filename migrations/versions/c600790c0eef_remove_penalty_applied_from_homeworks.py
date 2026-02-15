"""remove_penalty_applied_from_homeworks

Revision ID: c600790c0eef
Revises: 5ee9b89f14b3
Create Date: 2026-02-15 17:16:05.421136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c600790c0eef'
down_revision: Union[str, Sequence[str], None] = '5ee9b89f14b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('homeworks') as batch_op:
        batch_op.drop_column('penalty_applied')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('homeworks') as batch_op:
        batch_op.add_column(
            sa.Column('penalty_applied', sa.BOOLEAN(), nullable=False, server_default='0')
        )
