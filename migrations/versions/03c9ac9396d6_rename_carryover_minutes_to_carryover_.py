"""Rename carryover_minutes to carryover_out_minutes

Revision ID: 03c9ac9396d6
Revises: c2ee4c0ee174
Create Date: 2026-02-07 08:46:42.752069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03c9ac9396d6'
down_revision: Union[str, Sequence[str], None] = 'c2ee4c0ee174'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('weeks', 'carryover_minutes', new_column_name='carryover_out_minutes')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('weeks', 'carryover_out_minutes', new_column_name='carryover_minutes')
