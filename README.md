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

# EduPage credentials (optional)
EDUPAGE_USERNAME=your_email@example.com
EDUPAGE_PASSWORD=your_password
EDUPAGE_SUBDOMAIN=your_school_subdomain
EDUPAGE_SCHOOL=CZ
```

## Config System (SQLite)

Runtime configuration stored in the `configs` table. Managed via MCP tools (`get_config`, `set_config`, `list_configs`). Use `check_system_readiness` to verify all required configs are set.

### Entries with defaults (seeded by migration)

| Key | Default | Description |
|-----|---------|-------------|
| `GRADE_MINUTES_MAP` | `{"1":15,"2":10,"3":0,"4":-20,"5":-25}` | Grade → game minutes conversion |
| `TOPIC_REVIEW_THRESHOLDS` | `{"2":1,"3":2,"4":3,"5":3}` | Repetitions needed per grade before TopicReview is closed |
| `HOMEWORK_BONUS_MINUTES_ONTIME` | `10` | Bonus minutes for on-time homework |
| `HOMEWORK_BONUS_MINUTES_OVERDUE` | `-10` | Penalty minutes for overdue homework |
| `BONUS_FUND_WEEKLY_TOPUP` | `15` | Bonus task slots added each week |
| `DEFAULT_DEADLINE_TIME` | `20:00` | Default time when deadline has only a date |

### Required entries (must be set before use)

| Key | Description |
|-----|-------------|
| `TEMP_BOOK_DIR` | Folder where users place book files for processing |
| `BOOKS_STORAGE_DIR` | Base folder for storing processed books |
| `ISSUES_LOG` | Path to the issue log file |
| `FAMILY_LANGUAGE` | Language for communication with the family |

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

## MCP Tools (76 total)

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
- `check_pending_bonus_task` - check if there's a pending task to reuse

### Bonuses
- `create_bonus` - create a homework bonus record (+/- minutes)
- `delete_bonus` - delete a bonus record
- `list_unrewarded_bonuses` - list bonuses not yet included in weekly calc
- `mark_bonuses_rewarded` - mark bonuses as included in weekly calc

### Bonus Funds
- `get_bonus_fund` - get the bonus fund
- `add_tasks_to_fund` - add task slots to the fund

### Homework
- `create_homework` - create homework assignment
- `list_homeworks` - list homework (filter: status, subject)
- `complete_homework` - mark homework as done
- `update_homework` - update homework details
- `close_overdue_homeworks` - close overdue homework with penalty
- `get_pending_homework_reminders` - get reminders due (D-1, D-2)
- `mark_homework_reminders_sent` - mark reminders as sent

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
- `calculate_weekly_minutes` - calculate grade/bonus minutes for the week
- `get_grade_to_minutes_map` - get grade-to-minutes conversion table

### Topic Reviews
- `list_topic_reviews` - list topic reviews (filter: subject, status)
- `get_pending_reviews_for_topic` - get pending reviews for a topic
- `mark_topic_reinforced` - mark review as reinforced
- `increment_topic_repeat_count` - increment repeat count for a review
- `get_priority_topic_for_review` - pick a priority topic from top-4

### Family Members
- `create_family_member` - add a family member (student/parent/tutor/admin)
- `list_family_members` - list members (filter: role)
- `update_family_member` - update member details
- `delete_family_member` - delete a member
- `get_student` - get the student record

### Gateways
- `create_gateway` - register a messaging channel (Telegram, etc.)
- `list_gateways` - list gateways (filter: family_member, channel)
- `update_gateway` - update gateway details
- `delete_gateway` - delete a gateway
- `lookup_gateway` - find gateway by platform + external ID

### Configs
- `get_config` - get a config value by key
- `set_config` - set a config value (existing keys only)
- `list_configs` - list all config entries

### Readiness
- `check_system_readiness` - check if the system is properly configured (active schools, required configs)

### Escalation
- `get_grades_pending_escalation` - get grades needing parent notification
- `mark_grades_escalated` - mark grades as escalated (parent was notified)

### EduPage Sync
- `sync_edupage_grades` - sync grades from EduPage
- `sync_edupage_homeworks` - sync homework from EduPage

### Instruction Tools
- `get_grade_escalation_instructions` - escalate bad grades to tutor/admin
- `get_learning_system_instructions` - master instruction: full system rules
- `get_student_request_router_instructions` - classify student request (A/B/C scenarios)
- `get_bonus_task_assignment_instructions` - assign a new bonus task
- `get_submission_routing_instructions` - route submitted work to evaluator
- `get_bonus_task_evaluation_instructions` - evaluate completed bonus task
- `get_homework_evaluation_instructions` - evaluate homework submission
- `get_book_lookup_instructions` - find and deliver textbook pages
- `get_books_workflow_instructions` - process and register new books
- `get_homework_manual_instructions` - manually add homework (parent only)
- `get_grade_manual_instructions` - manually add a grade (adult only)
- `get_topic_review_curation_instructions` - curate and close stale topic reviews

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

[PolyForm Noncommercial 1.0.0](LICENSE)
