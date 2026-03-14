# AGENTS.md

## Build & Test

```bash
poetry install              # Install dependencies
poetry run alembic upgrade head  # Run migrations
poetry run pytest            # Run tests
poetry run ruff check .      # Lint
```

## Code Style

- **Imports**: Direct imports only, never use `__all__`
  ```python
  # Wrong:
  from learning_hub.models import Grade

  # Correct:
  from learning_hub.models.grade import Grade
  ```
- Line length: 100 characters (ruff enforced)
- Code comments in English
- Prefer readability over elegance

## Architecture

- **MCP server** (FastMCP) with SQLAlchemy 2.0 async ORM + aiosqlite
- **Instruction tools** return markdown algorithms guiding AI agents through workflows
- Tool names referenced via constants in `src/learning_hub/tools/tool_names.py`
- Config variable names in `src/learning_hub/tools/config_vars.py`
- Game minutes use an immutable transaction ledger — balance = SUM of all transactions

## SQLAlchemy Enum Caveat

If a `mapped_column` uses explicit `String(...)` type, SQLAlchemy returns a **string**, not an enum. Do not call `.value` on it — the value is already a string.

## Security

This is a **public repository**. Never commit sensitive data: real names, emails, phone numbers, API keys, server IPs, or any PII. Tests must use generic placeholder names.
