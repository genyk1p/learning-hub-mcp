# Learning Hub MCP

MCP server for student learning workflow with SQLite database.

## Features

- **Subjects** - school subjects with multi-country support (UA, CZ, DE, etc.)
- **Grades** - grade tracking with 5-point European scale (1=best, 5=worst)
- **Topics** - subject topics for improvement tracking
- **Homework** - assignment tracking with deadlines
- **Bonus Tasks** - motivational tasks that reward game minutes
- **Weeks** - weekly game time calculations based on performance
- **Books** - textbook library with markdown summaries and content indexing
- **Topic Reviews** - reinforcement tracking for weak topics
- **Escalation** - bad grade notifications for parents
- **Instruction Tools** - markdown algorithms that guide AI agents through workflows
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

## MCP Tools (47 total)

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
- `create_bonus_task` - create a bonus task linked to a topic
- `list_bonus_tasks` - list tasks (filter: status, topic)
- `get_bonus_task` - get a bonus task by ID
- `get_latest_bonus_task` - get the most recent bonus task
- `complete_bonus_task` - mark task as completed
- `apply_bonus_task_result` - complete task and update related topic reviews
- `cancel_bonus_task` - cancel a task

### Bonus Funds
- `get_bonus_fund` - get the bonus fund
- `add_tasks_to_fund` - add task slots to the fund

### Homework
- `create_homework` - create homework assignment
- `list_homeworks` - list homework (filter: status, subject)
- `complete_homework` - mark homework as done
- `update_homework` - update homework details

### Books
- `add_book` - add a book to the library
- `list_books` - list books (filter: subject, has_summary)
- `get_book` - get a book by ID
- `update_book` - update book details
- `delete_book` - delete a book

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

### Escalation
- `get_grades_pending_escalation` - get grades needing parent notification
- `mark_grades_escalated` - mark grades as escalated (parent was notified)

### EduPage Sync
- `sync_edupage_grades` - sync grades from EduPage
- `sync_edupage_homeworks` - sync homework from EduPage

### Instruction Tools
- `get_student_request_router_instructions` - classify student request (A/B/C scenarios)
- `get_bonus_task_assignment_instructions` - assign a new bonus task
- `get_submission_routing_instructions` - route submitted work to evaluator
- `get_bonus_task_evaluation_instructions` - evaluate completed bonus task
- `get_homework_evaluation_instructions` - evaluate homework submission
- `get_book_lookup_instructions` - find and deliver textbook pages
- `get_books_workflow_instructions` - process and register new books
- `get_homework_manual_instructions` - manually add homework (parent only)

## OpenClaw Bridge Plugin

The `learning-hub-bridge/` directory contains a TypeScript plugin that makes all MCP tools available as native [OpenClaw](https://github.com/open-claw/openclaw) agent tools.

### Why

OpenClaw doesn't support MCP servers natively. Without the bridge, the agent would need `exec + mcporter` — slow (~3s per call), buggy (mcporter serialization issues with lists), and invisible to the model (tools not in tool list).

### How it works

1. On gateway startup, the bridge spawns the Python MCP server as a child process (STDIO)
2. Discovers all tools via `client.listTools()` (MCP protocol)
3. Registers each as a native OpenClaw tool via `api.registerTool()` with prefix `learning_hub_`
4. Proxies `execute()` → `client.callTool()`, merging multiple TextContent blocks into a single JSON array
5. Auto-reconnects if the Python process dies

After this, the model sees `learning_hub_list_subjects`, `learning_hub_add_grade`, etc. directly in its tool list.

### Deployment

The bridge must be installed as an OpenClaw extension. The source lives in `learning-hub-bridge/` inside this repo, but OpenClaw loads plugins from `~/.openclaw/extensions/<pluginId>/`.

**Step 1.** Copy the bridge to extensions:

```bash
cp -r /path/to/learning-hub-mcp/learning-hub-bridge ~/.openclaw/extensions/learning-hub
```

**Step 2.** Install dependencies:

```bash
cd ~/.openclaw/extensions/learning-hub
npm install
```

**Step 3.** Add plugin config to `openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "learning-hub": {
        "enabled": true,
        "config": {
          "command": "/bin/bash",
          "args": ["-lc", "cd /path/to/learning-hub-mcp && exec .venv/bin/learning-hub-mcp"],
          "cwd": "/path/to/learning-hub-mcp",
          "toolPrefix": "learning_hub"
        }
      }
    }
  }
}
```

**Step 4.** Allow tools for the agent in `openclaw.json`:

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "tools": {
          "alsoAllow": ["learning-hub"]
        }
      }
    ]
  }
}
```

**Step 5.** Restart gateway:

```bash
openclaw gateway restart
```

### Config options

| Option | Description | Default |
|---|---|---|
| `command` | Command to start MCP server | (required) |
| `args` | Arguments for the command | (required) |
| `cwd` | Working directory for MCP server process | — |
| `toolPrefix` | Prefix for registered tool names | `learning_hub` |

### Updating after MCP changes

When new tools are added to the MCP server, the bridge picks them up automatically on gateway restart — no bridge code changes needed. Just restart:

```bash
openclaw gateway restart
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
