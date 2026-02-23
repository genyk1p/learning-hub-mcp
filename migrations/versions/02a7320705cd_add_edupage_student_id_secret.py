"""add_edupage_student_id_secret

Revision ID: 02a7320705cd
Revises: 49af2979d8a6
Create Date: 2026-02-23 18:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '02a7320705cd'
down_revision: Union[str, Sequence[str], None] = '49af2979d8a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add EDUPAGE_STUDENT_ID secret for parent account child matching."""
    op.execute(
        "INSERT INTO secrets (key, value, description, created_at, updated_at) "
        "VALUES ("
        "'EDUPAGE_STUDENT_ID', NULL, "
        "'EduPage student person_id (for parent accounts with multiple children)', "
        "datetime('now'), datetime('now'))"
    )


def downgrade() -> None:
    """Remove EDUPAGE_STUDENT_ID secret."""
    op.execute("DELETE FROM secrets WHERE key = 'EDUPAGE_STUDENT_ID'")
