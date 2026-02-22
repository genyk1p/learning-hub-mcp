"""generalize_external_id_and_add_pronote

Replace provider-specific edupage_id columns with generic
external_id + external_source on grades and homeworks tables.
Add attachment_url to homeworks. Seed PRONOTE sync provider.

Revision ID: 36e84c5b2e81
Revises: d65309f12f28
Create Date: 2026-02-22 15:05:19.283526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36e84c5b2e81'
down_revision: Union[str, Sequence[str], None] = 'd65309f12f28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # --- grades table ---
    # Add new columns
    op.add_column("grades", sa.Column("external_id", sa.String(100), nullable=True))
    op.add_column("grades", sa.Column("external_source", sa.String(20), nullable=True))

    # Migrate data from edupage_id
    conn.execute(sa.text(
        "UPDATE grades SET external_id = CAST(edupage_id AS TEXT), "
        "external_source = 'edupage' WHERE edupage_id IS NOT NULL"
    ))

    # Drop old column and create new unique constraint (SQLite batch mode)
    with op.batch_alter_table("grades") as batch_op:
        batch_op.drop_column("edupage_id")
        batch_op.create_unique_constraint(
            "uq_grades_external", ["external_id", "external_source"]
        )

    # --- homeworks table ---
    # Add new columns
    op.add_column("homeworks", sa.Column("external_id", sa.String(100), nullable=True))
    op.add_column("homeworks", sa.Column("external_source", sa.String(20), nullable=True))
    op.add_column("homeworks", sa.Column("attachment_url", sa.String(1000), nullable=True))

    # Migrate data from edupage_id
    conn.execute(sa.text(
        "UPDATE homeworks SET external_id = edupage_id, "
        "external_source = 'edupage' WHERE edupage_id IS NOT NULL"
    ))

    # Drop old column and create new unique constraint (SQLite batch mode)
    with op.batch_alter_table("homeworks") as batch_op:
        batch_op.drop_column("edupage_id")
        batch_op.create_unique_constraint(
            "uq_homeworks_external", ["external_id", "external_source"]
        )

    # --- Seed PRONOTE provider ---
    conn.execute(sa.text(
        "INSERT INTO sync_providers (code, name, is_active, school_id, "
        "created_at, updated_at) "
        "VALUES (:code, :name, 0, NULL, datetime('now'), datetime('now'))"
    ), {"code": "pronote", "name": "PRONOTE"})


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # Remove PRONOTE provider
    conn.execute(sa.text("DELETE FROM sync_providers WHERE code = 'pronote'"))

    # --- homeworks table ---
    op.add_column("homeworks", sa.Column("edupage_id", sa.String(50), nullable=True))
    conn.execute(sa.text(
        "UPDATE homeworks SET edupage_id = external_id "
        "WHERE external_source = 'edupage'"
    ))
    with op.batch_alter_table("homeworks") as batch_op:
        batch_op.drop_constraint("uq_homeworks_external", type_="unique")
        batch_op.drop_column("attachment_url")
        batch_op.drop_column("external_source")
        batch_op.drop_column("external_id")
        batch_op.create_unique_constraint("uq_homeworks_edupage_id", ["edupage_id"])

    # --- grades table ---
    op.add_column("grades", sa.Column("edupage_id", sa.Integer(), nullable=True))
    conn.execute(sa.text(
        "UPDATE grades SET edupage_id = CAST(external_id AS INTEGER) "
        "WHERE external_source = 'edupage'"
    ))
    with op.batch_alter_table("grades") as batch_op:
        batch_op.drop_constraint("uq_grades_external", type_="unique")
        batch_op.drop_column("external_source")
        batch_op.drop_column("external_id")
        batch_op.create_unique_constraint("uq_grades_edupage_id", ["edupage_id"])
