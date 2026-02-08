"""Remove bonus minutes system, switch to task slots

Revision ID: e1a2b3c4d5e6
Revises: 03c9ac9396d6
Create Date: 2026-02-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '03c9ac9396d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # bonus_funds: drop 'minutes', add 'available_tasks', add singleton constraint
    with op.batch_alter_table('bonus_funds') as batch_op:
        batch_op.drop_column('minutes')
        batch_op.add_column(sa.Column('available_tasks', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_check_constraint('ck_bonus_funds_singleton', 'id = 1')

    # bonus_tasks: drop 'minutes_promised', rename status enum value PROMISED -> PENDING
    with op.batch_alter_table('bonus_tasks') as batch_op:
        batch_op.drop_column('minutes_promised')

    # SQLite stores enum as text, so update existing rows directly
    op.execute("UPDATE bonus_tasks SET status = 'PENDING' WHERE status = 'PROMISED'")

    # weeks: drop 'bonus_minutes'
    with op.batch_alter_table('weeks') as batch_op:
        batch_op.drop_column('bonus_minutes')


def downgrade() -> None:
    """Downgrade schema."""
    # weeks: restore 'bonus_minutes'
    with op.batch_alter_table('weeks') as batch_op:
        batch_op.add_column(sa.Column('bonus_minutes', sa.Integer(), nullable=False, server_default='0'))

    # bonus_tasks: restore 'minutes_promised', rename status back
    op.execute("UPDATE bonus_tasks SET status = 'PROMISED' WHERE status = 'PENDING'")
    with op.batch_alter_table('bonus_tasks') as batch_op:
        batch_op.add_column(sa.Column('minutes_promised', sa.Integer(), nullable=False, server_default='0'))

    # bonus_funds: restore 'minutes', drop 'available_tasks', drop singleton constraint
    with op.batch_alter_table('bonus_funds') as batch_op:
        batch_op.drop_constraint('ck_bonus_funds_singleton', type_='check')
        batch_op.drop_column('available_tasks')
        batch_op.add_column(sa.Column('minutes', sa.Integer(), nullable=False, server_default='0'))
