"""Initial schema.

Creates all tables for the Learning Hub system:
schools, subjects, subject_topics, grades, bonus_tasks, homeworks,
minute_transactions, books, topic_reviews, family_members, gateways,
configs, secrets, sync_providers.

Revision ID: 0001
Revises: -
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "schools",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("grading_system", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "family_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "PARENT", "STUDENT", "TUTOR", "RELATIVE",
                    name="familyrole"),
            nullable=False,
        ),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_student", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "NOT (is_student = 1 AND is_admin = 1)",
            name="check_student_not_admin",
        ),
        sa.CheckConstraint(
            "NOT (is_student = 1 AND full_name IS NULL)",
            name="check_student_has_full_name",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("family_members") as batch_op:
        batch_op.create_index(
            "uq_single_student", ["is_student"], unique=True,
            sqlite_where=sa.text("is_student = 1"),
        )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_path", sa.String(500), nullable=True),
        sa.Column("summary_path", sa.String(500), nullable=True),
        sa.Column("contents_path", sa.String(500), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_ru", sa.String(100), nullable=True),
        sa.Column("grade_level", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("current_book_id", sa.Integer(), nullable=True),
        sa.Column("tutor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "grade_level IS NULL OR (grade_level >= 1 AND grade_level <= 20)",
            name="check_grade_level_range",
        ),
        sa.ForeignKeyConstraint(["current_book_id"], ["books.id"],
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["tutor_id"], ["family_members.id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "name", "grade_level",
                            name="uq_subject_school_name_grade"),
    )

    op.create_table(
        "gateways",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("family_member_id", sa.Integer(), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("TELEGRAM", "WHATSAPP", "DISCORD", "SLACK", "SIGNAL",
                    "IMESSAGE", "MSTEAMS", "MATRIX", name="channeltype"),
            nullable=False,
        ),
        sa.Column("channel_uid", sa.String(100), nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_member_id"], ["family_members.id"],
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "channel_uid", name="uq_channel_uid"),
    )
    with op.batch_alter_table("gateways") as batch_op:
        batch_op.create_index(
            "uq_default_per_member", ["family_member_id"], unique=True,
            sqlite_where=sa.text("is_default = 1"),
        )

    op.create_table(
        "subject_topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "close_reason",
            sa.Enum("RESOLVED", "SKIPPED", "NO_LONGER_RELEVANT",
                    name="closereason"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id", "description",
                            name="uq_subject_topic_subject_description"),
    )

    op.create_table(
        "sync_providers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("is_active = 0 OR school_id IS NOT NULL",
                           name="ck_active_requires_school"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"],
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("school_id"),
    )

    op.create_table(
        "bonus_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_topic_id", sa.Integer(), nullable=False),
        sa.Column("task_description", sa.String(1000), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "CANCELLED",
                    name="bonustaskstatus"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subject_topic_id"], ["subject_topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "homeworks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("subject_topic_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "DONE", "OVERDUE", name="homeworkstatus"),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recommended_grade",
            sa.Enum("EXCELLENT", "GOOD", "SATISFACTORY", "POOR", "FAIL",
                    name="gradevalue"),
            nullable=True,
        ),
        sa.Column("book_id", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("external_source", sa.String(20), nullable=True),
        sa.Column("attachment_url", sa.String(1000), nullable=True),
        sa.Column("reminded_d2_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminded_d1_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"],
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["subject_topic_id"], ["subject_topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", "external_source",
                            name="uq_homeworks_external"),
    )

    op.create_table(
        "grades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("subject_topic_id", sa.Integer(), nullable=True),
        sa.Column("bonus_task_id", sa.Integer(), nullable=True),
        sa.Column("homework_id", sa.Integer(), nullable=True),
        sa.Column(
            "grade_value",
            sa.Enum("EXCELLENT", "GOOD", "SATISFACTORY", "POOR", "FAIL",
                    name="gradevalue"),
            nullable=False,
        ),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("external_source", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bonus_task_id"], ["bonus_tasks.id"]),
        sa.ForeignKeyConstraint(["homework_id"], ["homeworks.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["subject_topic_id"], ["subject_topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", "external_source",
                            name="uq_grades_external"),
        sa.UniqueConstraint("bonus_task_id", name="uq_grades_bonus_task_id"),
        sa.UniqueConstraint("homework_id", name="uq_grades_homework_id"),
    )

    op.create_table(
        "topic_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("subject_topic_id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "REINFORCED", name="topicreviewstatus"),
            nullable=False,
        ),
        sa.Column("repeat_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["subject_topic_id"], ["subject_topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grade_id"),
    )

    op.create_table(
        "minute_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("grade_id", sa.Integer(), nullable=True),
        sa.Column("homework_id", sa.Integer(), nullable=True),
        sa.Column("bonus_task_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"]),
        sa.ForeignKeyConstraint(["homework_id"], ["homeworks.id"]),
        sa.ForeignKeyConstraint(["bonus_task_id"], ["bonus_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("homework_id",
                            name="uq_minute_transactions_homework_id"),
        sa.UniqueConstraint("bonus_task_id",
                            name="uq_minute_transactions_bonus_task_id"),
    )


def downgrade() -> None:
    op.drop_table("minute_transactions")
    op.drop_table("topic_reviews")
    op.drop_table("grades")
    op.drop_table("homeworks")
    op.drop_table("bonus_tasks")
    op.drop_table("sync_providers")
    op.drop_table("subject_topics")
    with op.batch_alter_table("gateways") as batch_op:
        batch_op.drop_index("uq_default_per_member",
                            sqlite_where=sa.text("is_default = 1"))
    op.drop_table("gateways")
    op.drop_table("subjects")
    op.drop_table("books")
    with op.batch_alter_table("family_members") as batch_op:
        batch_op.drop_index("uq_single_student",
                            sqlite_where=sa.text("is_student = 1"))
    op.drop_table("family_members")
    op.drop_table("schools")
    op.drop_table("secrets")
    op.drop_table("configs")
