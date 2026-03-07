"""Seed default data.

Seeds configs, schools, secrets, and sync providers with initial values.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-01
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed default data: configs, schools, secrets, sync providers."""

    # --- Configs with defaults ---
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('GRADE_MINUTES_MAP', "
        "'{\"1\": 15, \"2\": 10, \"3\": 0, \"4\": -20, \"5\": -25}', "
        "'Grade to game minutes conversion (JSON: grade_value -> minutes)', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('TOPIC_REVIEW_THRESHOLDS', "
        "'{\"2\": 1, \"3\": 2, \"4\": 3, \"5\": 3}', "
        "'Required repetitions per grade before TopicReview is closed (JSON)', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('HOMEWORK_BONUS_MINUTES_ONTIME', '10', "
        "'Bonus minutes for completing homework on time', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('HOMEWORK_BONUS_MINUTES_OVERDUE', '-10', "
        "'Penalty minutes for overdue homework', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('MAX_PENDING_BONUS_TASKS', '4', "
        "'Maximum number of pending bonus tasks at the same time', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('MAX_COMPLETED_BONUS_TASKS_PER_WEEK', '15', "
        "'Maximum bonus tasks completed in a rolling 7-day window', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('DEFAULT_DEADLINE_TIME', '20:00', "
        "'Default time when deadline is date-only (HH:MM)', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('SETUP_COMPLETED', 'false', "
        "'Whether initial setup has been completed', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('BASE_CRONS_INSTALLED', 'false', "
        "'Whether base cron jobs have been created', "
        "0, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('SYNC_CRON_CONFIGURED', 'false', "
        "'Whether a sync cron job has been created after first successful sync', "
        "0, datetime('now'), datetime('now'))"
    )

    # --- Configs required (NULL values) ---
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('TEMP_BOOK_DIR', NULL, "
        "'Staging folder where users place book files for processing', "
        "1, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('BOOKS_STORAGE_DIR', NULL, "
        "'Base folder for storing processed books', "
        "1, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('ISSUES_LOG', NULL, "
        "'Path to the issue log file for logging problems', "
        "1, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO configs (key, value, description, is_required, "
        "created_at, updated_at) VALUES "
        "('FAMILY_LANGUAGE', NULL, "
        "'Language for communication with the family (e.g. русский)', "
        "1, datetime('now'), datetime('now'))"
    )

    # --- Schools (17 countries, all inactive) ---
    schools = [
        ("CZ", "Česká škola",
         "Stupnice 1–5 (1 nejlepší, 5 nejhorší). Používá se také mezistupně: "
         "1+, 1-, 2+, 2- atd. Shodná se stupnicí MCP — konverze není nutná."),
        ("UA", "Українська школа",
         "Шкала 1–12 (12 найкраща). Конвертація в MCP (1-5): "
         "10-12→1, 7-9→2, 4-6→3, 2-3→4, 1→5."),
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
        ("CH", "Schweizer Schule",
         "Notensystem 1–6 (6 beste Note, 1 schlechteste). "
         "Konvertierung in MCP (1-5): 6→1, 5→2, 4→3, 3→4, 1-2→5."),
    ]
    for code, name, grading in schools:
        grading_escaped = grading.replace("'", "''")
        name_escaped = name.replace("'", "''")
        op.execute(
            f"INSERT INTO schools (code, name, grading_system, is_active, "
            f"created_at, updated_at) VALUES "
            f"('{code}', '{name_escaped}', '{grading_escaped}', "
            f"0, datetime('now'), datetime('now'))"
        )

    # --- Secrets (all NULL values) ---
    secrets = [
        ("EDUPAGE_USERNAME", "EduPage account email/username"),
        ("EDUPAGE_PASSWORD", "EduPage account password"),
        ("EDUPAGE_SUBDOMAIN", "EduPage school subdomain (e.g. zsluhacovice)"),
        ("EDUPAGE_STUDENT_ID",
         "EduPage student person_id (for parent accounts with multiple children)"),
        ("PRONOTE_URL",
         "PRONOTE instance URL (e.g. https://xxx.index-education.net/pronote/eleve.html)"),
        ("PRONOTE_USERNAME", "PRONOTE account username"),
        ("PRONOTE_PASSWORD", "PRONOTE account password"),
    ]
    for key, desc in secrets:
        desc_escaped = desc.replace("'", "''")
        op.execute(
            f"INSERT INTO secrets (key, value, description, "
            f"created_at, updated_at) VALUES "
            f"('{key}', NULL, '{desc_escaped}', "
            f"datetime('now'), datetime('now'))"
        )

    # --- Sync Providers (all inactive) ---
    op.execute(
        "INSERT INTO sync_providers "
        "(code, name, is_active, school_id, created_at, updated_at) VALUES "
        "('edupage', 'EduPage', 0, NULL, datetime('now'), datetime('now'))"
    )
    op.execute(
        "INSERT INTO sync_providers "
        "(code, name, is_active, school_id, created_at, updated_at) VALUES "
        "('pronote', 'PRONOTE', 0, NULL, datetime('now'), datetime('now'))"
    )


def downgrade() -> None:
    """Remove all seed data."""
    op.execute("DELETE FROM sync_providers WHERE code IN ('edupage', 'pronote')")
    op.execute(
        "DELETE FROM secrets WHERE key IN ("
        "'EDUPAGE_USERNAME', 'EDUPAGE_PASSWORD', 'EDUPAGE_SUBDOMAIN', "
        "'EDUPAGE_STUDENT_ID', "
        "'PRONOTE_URL', 'PRONOTE_USERNAME', 'PRONOTE_PASSWORD')"
    )
    op.execute(
        "DELETE FROM schools WHERE code IN ("
        "'CZ', 'UA', 'SK', 'AT', 'DE', 'FR', 'GB', 'ES', "
        "'IT', 'PL', 'NL', 'US', 'CA', 'AR', 'BR', 'AU', 'CH')"
    )
    op.execute(
        "DELETE FROM configs WHERE key IN ("
        "'GRADE_MINUTES_MAP', 'TOPIC_REVIEW_THRESHOLDS', "
        "'HOMEWORK_BONUS_MINUTES_ONTIME', 'HOMEWORK_BONUS_MINUTES_OVERDUE', "
        "'MAX_PENDING_BONUS_TASKS', 'MAX_COMPLETED_BONUS_TASKS_PER_WEEK', "
        "'DEFAULT_DEADLINE_TIME', 'SETUP_COMPLETED', "
        "'BASE_CRONS_INSTALLED', 'SYNC_CRON_CONFIGURED', "
        "'TEMP_BOOK_DIR', 'BOOKS_STORAGE_DIR', 'ISSUES_LOG', 'FAMILY_LANGUAGE')"
    )
