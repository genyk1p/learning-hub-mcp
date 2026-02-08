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
- `get_bonus_task` - get a bonus task by ID
- `get_latest_bonus_task` - get the most recent bonus task
- `complete_bonus_task` - mark task as completed
- `apply_bonus_task_result` - complete task and update related topic reviews
- `cancel_bonus_task` - cancel a task

### Bonus Funds
- `create_bonus_fund` - create a new bonus fund
- `list_bonus_funds` - list all bonus funds
- `add_minutes_to_fund` - add minutes to a fund
- `rename_bonus_fund` - rename a fund

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

### Topic Reviews
- `list_topic_reviews` - list topic reviews (filter: subject, status)
- `get_pending_reviews_for_topic` - get pending reviews for a topic
- `mark_topic_reinforced` - mark review as reinforced
- `increment_topic_repeat_count` - increment repeat count for a review

### Books
- `add_book` - add a book to the library
- `list_books` - list books (filter: subject, has_summary)
- `get_book` - get a book by ID
- `update_book` - update book details
- `delete_book` - delete a book

### EduPage Sync
- `sync_edupage_grades` - sync grades from EduPage
- `sync_edupage_homeworks` - sync homework from EduPage

## OpenClaw Integration

The `learning-hub-bridge/` directory contains a TypeScript plugin that makes all MCP tools available as native OpenClaw agent tools. Instead of calling the MCP server through `exec + mcporter`, the model sees tools like `learning_hub_list_subjects` directly in its tool list.

### Setup

```bash
cd learning-hub-bridge
npm install
```

### OpenClaw config (`openclaw.json`)

```json
{
  "plugins": {
    "entries": {
      "learning-hub": {
        "enabled": true,
        "command": "/bin/bash",
        "args": ["-lc", "cd /path/to/learning-hub-mcp && exec .venv/bin/learning-hub-mcp"],
        "cwd": "/path/to/learning-hub-mcp"
      }
    }
  }
}
```

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
