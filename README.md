# Learning Hub MCP

MCP server for student learning workflow with SQLite database.

## Features

- **Subjects** - school subjects with multi-country support (UA, CZ, DE, etc.)
- **Grades** - grade tracking with 5-point European scale (1=best, 5=worst)
- **Topics** - subject topics for improvement tracking
- **Homework** - assignment tracking with deadlines
- **Bonus Tasks** - motivational tasks that reward game minutes
- **Weeks** - weekly game time calculations based on performance
- **EduPage Sync** - automatic sync of grades and homework from EduPage

## Installation

```bash
# Install dependencies
poetry install

# Initialize database
poetry run alembic upgrade head
```

## Configuration

Create `.env` file (see `.env.example`):

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/learning_hub.db

# Timezone
TIMEZONE=Europe/Vienna

# EduPage credentials (optional)
EDUPAGE_USERNAME=your_email@example.com
EDUPAGE_PASSWORD=your_password
EDUPAGE_SUBDOMAIN=your_school_subdomain
EDUPAGE_SCHOOL=CZ
```

## Usage

### Run MCP Server

```bash
poetry run learning-hub-mcp
```

### MCP Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "learning-hub": {
      "command": "poetry",
      "args": ["run", "learning-hub-mcp"],
      "cwd": "/path/to/learning-hub-mcp"
    }
  }
}
```

## MCP Tools

### Subjects
- `create_subject` - create a new school subject
- `list_subjects` - list subjects (filter: school, is_active)
- `update_subject` - update subject details

### Topics
- `create_topic` - create a topic for a subject
- `list_topics` - list topics (filter: subject_id, is_open)
- `close_topic` - close topic (reason: resolved/skipped/no_longer_relevant)

### Grades
- `add_grade` - add a grade (1-5 scale, 1=best)
- `list_grades` - list grades (filter: subject, date range, school)
- `update_grade` - update grade details

### Bonus Tasks
- `create_bonus_task` - create a bonus task with promised game minutes
- `list_bonus_tasks` - list tasks (filter: status, topic)
- `complete_bonus_task` - mark task as completed
- `cancel_bonus_task` - cancel a task

### Homework
- `create_homework` - create homework assignment
- `list_homeworks` - list homework (filter: status, subject)
- `complete_homework` - mark homework as done
- `update_homework` - update homework details

### Weeks
- `create_week` - create a new week period
- `get_week` - get week by key or current week
- `update_week` - update week minutes
- `finalize_week` - finalize week and calculate carryover

### EduPage Sync
- `sync_edupage_grades` - sync grades from EduPage
- `sync_edupage_homeworks` - sync homework from EduPage

## Development

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=learning_hub

# Lint code
poetry run ruff check .

# Fix lint issues
poetry run ruff check --fix .
```

## License

MIT
