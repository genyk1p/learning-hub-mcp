"""add_book_id_to_homeworks

Revision ID: b491c39a36b3
Revises: e626294affbc
Create Date: 2026-02-13 19:03:35.229530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b491c39a36b3'
down_revision: Union[str, Sequence[str], None] = 'e626294affbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('homeworks') as batch_op:
        batch_op.add_column(sa.Column('book_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_homeworks_book_id', 'books', ['book_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('homeworks') as batch_op:
        batch_op.drop_constraint('fk_homeworks_book_id', type_='foreignkey')
        batch_op.drop_column('book_id')
