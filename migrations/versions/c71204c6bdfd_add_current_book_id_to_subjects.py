"""add_current_book_id_to_subjects

Revision ID: c71204c6bdfd
Revises: cd1012057b20
Create Date: 2026-02-13 19:51:07.476341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c71204c6bdfd'
down_revision: Union[str, Sequence[str], None] = 'cd1012057b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.add_column(sa.Column('current_book_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_subjects_current_book_id', 'books', ['current_book_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.drop_constraint('fk_subjects_current_book_id', type_='foreignkey')
        batch_op.drop_column('current_book_id')
