"""student_requires_full_name

Revision ID: 49af2979d8a6
Revises: 68fe7e62f88b
Create Date: 2026-02-23 18:11:28.747132

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '49af2979d8a6'
down_revision: Union[str, Sequence[str], None] = '68fe7e62f88b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CHECK constraint: student must have full_name."""
    # SQLite doesn't support ADD CONSTRAINT, so we use batch mode
    with op.batch_alter_table("family_members") as batch_op:
        batch_op.create_check_constraint(
            "check_student_has_full_name",
            "NOT (is_student = 1 AND full_name IS NULL)",
        )


def downgrade() -> None:
    """Remove CHECK constraint."""
    with op.batch_alter_table("family_members") as batch_op:
        batch_op.drop_constraint("check_student_has_full_name", type_="check")
