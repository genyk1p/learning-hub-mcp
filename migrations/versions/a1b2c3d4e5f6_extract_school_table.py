"""extract school into separate table

Revision ID: a1b2c3d4e5f6
Revises: 8cf801318955
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8cf801318955'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create schools table, migrate data from subjects.school column."""
    # 1. Create schools table
    op.create_table(
        'schools',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=2), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('grading_system', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    # 2. Seed all schools with grading system descriptions
    conn = op.get_bind()
    schools = [
        ("CZ", "Česká škola",
         "Stupnice 1–5 (1 nejlepší, 5 nejhorší). "
         "Používá se také mezistupně: 1+, 1-, 2+, 2- atd. "
         "Shodná se stupnicí MCP — konverze není nutná."),
        ("UA", "Українська школа",
         "Шкала 1–12 (12 найкраща). "
         "Конвертація в MCP (1-5): 10-12→1, 7-9→2, 4-6→3, 2-3→4, 1→5."),
        ("SK", "Slovenská škola",
         "Stupnica 1–5 (1 najlepšia, 5 najhoršia). "
         "Zhodná so stupnicou MCP — konverzia nie je potrebná."),
        ("AT", "Österreichische Schule",
         "Notensystem 1–5 (1 Sehr gut, 5 Nicht genügend). "
         "Identisch mit MCP-Skala — keine Konvertierung nötig."),
        ("DE", "Deutsche Schule",
         "Notensystem 1–6 (1 sehr gut, 6 ungenügend). "
         "Konvertierung in MCP (1-5): 1→1, 2→2, 3→3, 4→4, 5-6→5."),
        ("FR", "École française",
         "Échelle 0–20 (20 meilleure note). "
         "Conversion en MCP (1-5): 16-20→1, 14-15→2, 12-13→3, 8-11→4, 0-7→5."),
        ("GB", "British school",
         "GCSE scale 9–1 (9 highest). "
         "Conversion to MCP (1-5): 8-9→1, 6-7→2, 4-5→3, 2-3→4, 1→5."),
        ("ES", "Escuela española",
         "Escala 0–10 (10 mejor nota). "
         "Conversión a MCP (1-5): 9-10→1, 7-8→2, 5-6→3, 3-4→4, 0-2→5."),
        ("IT", "Scuola italiana",
         "Scala 1–10 (10 migliore). "
         "Conversione in MCP (1-5): 9-10→1, 7-8→2, 6→3, 4-5→4, 1-3→5."),
        ("PL", "Szkoła polska",
         "Skala 1–6 (6 celujący, 1 niedostateczny). "
         "Konwersja do MCP (1-5): 6→1, 5→2, 4→3, 3→4, 1-2→5."),
        ("NL", "Nederlandse school",
         "Schaal 1–10 (10 beste cijfer). "
         "Conversie naar MCP (1-5): 9-10→1, 8→2, 6-7→3, 5→4, 1-4→5."),
        ("US", "American school",
         "Letter grades A–F (A best). "
         "Conversion to MCP (1-5): A→1, B→2, C→3, D→4, F→5."),
        ("CA", "Canadian school",
         "Letter grades A–F (A best). "
         "Conversion to MCP (1-5): A→1, B→2, C→3, D→4, F→5."),
        ("AR", "Escuela argentina",
         "Escala 1–10 (10 mejor nota). "
         "Conversión a MCP (1-5): 9-10→1, 7-8→2, 5-6→3, 3-4→4, 1-2→5."),
        ("BR", "Escola brasileira",
         "Escala 0–10 (10 melhor nota). "
         "Conversão para MCP (1-5): 9-10→1, 7-8→2, 5-6→3, 3-4→4, 0-2→5."),
        ("AU", "Australian school",
         "Grades A–E (A highest). "
         "Conversion to MCP (1-5): A→1, B→2, C→3, D→4, E→5."),
    ]
    for code, name, gs in schools:
        conn.execute(sa.text(
            "INSERT INTO schools (code, name, grading_system, is_active, "
            "created_at, updated_at) "
            "VALUES (:code, :name, :gs, 0, datetime('now'), datetime('now'))"
        ), {"code": code, "name": name, "gs": gs})

    # 3. Add school_id column (nullable for now)
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.add_column(sa.Column('school_id', sa.Integer(), nullable=True))

    # 4. Populate school_id from existing school column
    conn.execute(sa.text(
        "UPDATE subjects SET school_id = ("
        "  SELECT id FROM schools WHERE code = subjects.school"
        ")"
    ))

    # 5. Finalize: make school_id NOT NULL, add FK, update unique constraint, drop school
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.alter_column('school_id', nullable=False)
        batch_op.create_foreign_key(
            'fk_subjects_school_id', 'schools', ['school_id'], ['id']
        )
        batch_op.drop_constraint('uq_subject_school_name_grade', type_='unique')
        batch_op.create_unique_constraint(
            'uq_subject_school_name_grade', ['school_id', 'name', 'grade_level']
        )
        batch_op.drop_column('school')


def downgrade() -> None:
    """Restore school column in subjects, drop schools table."""
    # 1. Add school column back (nullable for now)
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.add_column(sa.Column('school', sa.String(), nullable=True))

    # 2. Populate school from school_id
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE subjects SET school = ("
        "  SELECT code FROM schools WHERE id = subjects.school_id"
        ")"
    ))

    # 3. Finalize: make school NOT NULL, drop school_id, restore constraints
    with op.batch_alter_table('subjects') as batch_op:
        batch_op.alter_column('school', nullable=False)
        batch_op.drop_constraint('fk_subjects_school_id', type_='foreignkey')
        batch_op.drop_constraint('uq_subject_school_name_grade', type_='unique')
        batch_op.create_unique_constraint(
            'uq_subject_school_name_grade', ['school', 'name', 'grade_level']
        )
        batch_op.drop_column('school_id')

    # 4. Drop schools table
    op.drop_table('schools')
