"""Add minute_transactions table, drop bonuses/weeks/bonus_funds tables.

Replaces the bonus+rewarded+week+bonus_fund system with a transaction ledger
and config-based limits.

- minute_transactions: each event creates a transaction immediately.
  Balance = SUM(minutes) across all records.
- bonus_funds table dropped: replaced by MAX_PENDING_BONUS_TASKS and
  MAX_COMPLETED_BONUS_TASKS_PER_WEEK configs (computed from real data).
- fund_id column dropped from bonus_tasks (no longer needed).
- weeks and bonuses tables dropped (replaced by transaction ledger).
- grades.rewarded column dropped (transactions replace the rewarded flag).

IMPORTANT: Before running this migration on production (eva), run
calculate_weekly_minutes one last time to flush all unrewarded grades/bonuses.
Otherwise accumulated unrewarded records will be lost.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    r = conn.execute(sa.text(
        f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{name}'"
    ))
    return r.fetchone() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(sa.text(f"PRAGMA table_info({table})"))
    return column in [r[1] for r in rows]


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "minute_transactions"):
        op.create_table(
            "minute_transactions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("minutes", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("grade_id", sa.Integer(), sa.ForeignKey("grades.id"), nullable=True),
            sa.Column("homework_id", sa.Integer(), sa.ForeignKey("homeworks.id"), nullable=True),
            sa.Column("bonus_task_id", sa.Integer(), sa.ForeignKey("bonus_tasks.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("homework_id", name="uq_minute_transactions_homework_id"),
            sa.UniqueConstraint("bonus_task_id", name="uq_minute_transactions_bonus_task_id"),
        )

    # All drops are conditional — prod DB may differ from dev after squash
    if _column_exists(conn, "grades", "rewarded"):
        with op.batch_alter_table("grades") as batch_op:
            batch_op.drop_column("rewarded")

    if _table_exists(conn, "bonuses"):
        op.drop_table("bonuses")

    if _table_exists(conn, "weeks"):
        op.drop_table("weeks")

    if _column_exists(conn, "bonus_tasks", "fund_id"):
        with op.batch_alter_table("bonus_tasks") as batch_op:
            batch_op.drop_column("fund_id")

    if _table_exists(conn, "bonus_funds"):
        op.drop_table("bonus_funds")

    # Seed new config-based limits (replacing the mutable bonus_funds counter)
    op.execute(
        "INSERT OR IGNORE INTO configs "
        "(key, value, description, is_required, created_at, updated_at) "
        "VALUES "
        "('MAX_PENDING_BONUS_TASKS', '4', "
        "'Maximum number of pending bonus tasks at the same time', 0, "
        "datetime('now'), datetime('now')), "
        "('MAX_COMPLETED_BONUS_TASKS_PER_WEEK', '15', "
        "'Maximum bonus tasks completed in a rolling 7-day window', 0, "
        "datetime('now'), datetime('now'))"
    )


def downgrade() -> None:
    op.create_table(
        "weeks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("week_key", sa.String(20), nullable=False, unique=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grade_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("homework_bonus_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("carryover_out_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_played_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_finalized", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "bonuses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("homework_id", sa.Integer(), sa.ForeignKey("homeworks.id"), nullable=True, unique=True),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("rewarded", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column(
        "grades",
        sa.Column("rewarded", sa.Boolean(), nullable=False, server_default="0"),
    )

    op.drop_table("minute_transactions")

    # Remove config-based limits
    op.execute(
        "DELETE FROM configs WHERE key IN "
        "('MAX_PENDING_BONUS_TASKS', 'MAX_COMPLETED_BONUS_TASKS_PER_WEEK')"
    )

    # Recreate bonus_funds table
    op.create_table(
        "bonus_funds",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("available_tasks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_bonus_funds_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Restore fund_id column on bonus_tasks
    with op.batch_alter_table("bonus_tasks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "fund_id",
                sa.Integer(),
                sa.ForeignKey("bonus_funds.id"),
                nullable=True,
            )
        )
