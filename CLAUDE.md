# Learning Hub MCP

MCP server for managing student learning workflow - grades, homework, bonus tasks, and game time rewards.

## Project Structure

```
src/learning_hub/
├── server.py          # FastMCP server entry point
├── config.py          # Pydantic settings configuration
├── models/            # SQLAlchemy models
│   ├── base.py        # Base model with timestamps
│   ├── enums.py       # Enums (SchoolType, GradeValue, etc.)
│   ├── subject.py     # School subjects
│   ├── subject_topic.py # Topics within subjects
│   ├── grade.py       # Student grades
│   ├── bonus_task.py  # Bonus tasks for extra game time
│   ├── homework.py    # Homework assignments
│   └── week.py        # Weekly game time calculations
├── repositories/      # Data access layer (async SQLAlchemy)
├── tools/             # MCP tool definitions
│   ├── subjects.py
│   ├── subject_topics.py
│   ├── grades.py
│   ├── bonus_tasks.py
│   ├── homeworks.py
│   ├── weeks.py
│   └── edupage.py     # EduPage sync tools
└── database/          # Database session management
```

## Tech Stack

- **Python 3.12+**
- **FastMCP** - MCP server framework
- **SQLAlchemy 2.0** - async ORM
- **aiosqlite** - async SQLite driver
- **Alembic** - database migrations
- **edupage-api** - EduPage integration
- **Pydantic** - settings and validation

## Commands

```bash
# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Run MCP server
poetry run learning-hub-mcp

# Run tests
poetry run pytest

# Lint code
poetry run ruff check .
```

## Grade System

Uses 5-point European scale (1=best, 5=worst):
- 1 = Excellent (A)
- 2 = Good (B)
- 3 = Satisfactory (C)
- 4 = Poor (D)
- 5 = Fail (F)

## Week System

Weeks run Saturday to Saturday. Game minutes are calculated based on grades and bonus tasks.

## Development Rules

### Language
- Communication: **Russian**
- Code comments: **English**

### Imports
- **Never use `__all__`**
- **Only direct imports** - no magic
```python
# Wrong:
from learning_hub.models import Grade

# Correct:
from learning_hub.models.grade import Grade
```

### Code Style
- Prefer **readability** over elegance
- Keep code **simple and clear**
- Explicit is better than implicit
- Line length: 100 characters (ruff config)
