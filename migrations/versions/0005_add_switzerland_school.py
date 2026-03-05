"""Add Switzerland (CH) school.

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Switzerland school."""
    op.execute(
        "INSERT INTO schools (code, name, grading_system, is_active, "
        "created_at, updated_at) VALUES "
        "('CH', 'Schweizer Schule', "
        "'Notensystem 1–6 (6 beste Note, 1 schlechteste). "
        "Konvertierung in MCP (1-5): 6→1, 5→2, 4→3, 3→4, 1-2→5.', "
        "0, datetime('now'), datetime('now'))"
    )


def downgrade() -> None:
    """Remove Switzerland school."""
    op.execute("DELETE FROM schools WHERE code = 'CH'")
