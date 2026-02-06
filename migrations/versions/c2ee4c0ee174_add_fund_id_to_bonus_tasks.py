"""Add fund_id to bonus_tasks

Revision ID: c2ee4c0ee174
Revises: 8c14fc7de7b9
Create Date: 2026-02-06 22:57:34.009545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2ee4c0ee174'
down_revision: Union[str, Sequence[str], None] = '8c14fc7de7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('bonus_tasks') as batch_op:
        batch_op.add_column(sa.Column('fund_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_bonus_tasks_fund_id', 'bonus_funds', ['fund_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('bonus_tasks') as batch_op:
        batch_op.drop_constraint('fk_bonus_tasks_fund_id', type_='foreignkey')
        batch_op.drop_column('fund_id')
