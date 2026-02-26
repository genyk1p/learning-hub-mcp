"""Base cron jobs setup instruction — guides agent through creating base crons."""

from learning_hub.tools.config_vars import CFG_BASE_CRONS_INSTALLED
from learning_hub.tools.tool_names import TOOL_SET_CONFIG

BASE_CRONS_SETUP_INSTRUCTIONS = f"""\
# Base cron jobs setup

> Call this tool once after `check_system_readiness` returns `ready=true`.
>
> If config `{CFG_BASE_CRONS_INSTALLED}=true` — base crons are already set up. \
Do NOT call this tool again. Stop.

---

## Overview

Base crons keep the system running automatically:
- Homework deadline reminders sent to the student
- Reminder to the admin to close the previous week (if not finalized)
- Weekly game minutes calculation every Saturday
- Daily nudge encouraging the student to do a bonus task

These 4 crons are required regardless of whether a sync provider (EduPage, etc.)
is configured. Sync-specific crons are set up separately.

---

## Step 1 — Check communication channels

Call `list_family_members()`. Find the student (`is_student=true`) and the admin (`is_admin=true`).

Check that each has a `gateway_id` set:

**If the student has no `gateway_id`:**
Inform the user: student crons (homework reminders, bonus nudges) are useless without \
a communication channel — notifications won't be delivered. \
Set up a gateway for the student via `create_gateway` and link it via `update_family_member`. \
**Do NOT create crons — stop and help set up the gateway first.**

**If the admin has no `gateway_id`:**
Inform the user: admin crons (weekly summary, unfinalized week reminder) won't be able \
to send notifications. Set up a gateway for the admin first. \
**Do NOT create crons — stop and help set up the gateway first.**

**If both channels are configured** — proceed to step 2.

---

## Step 2 — Show schedule and get confirmation

Before creating, show the user all 4 crons with their default schedules and ask for confirmation.

| Cron | Schedule | Recipient | Reschedule? |
|------|----------|-----------|-------------|
| A — Homework reminders | Mon–Fri 17:00 | student | allowed |
| B — Unfinalized week | Wednesday 12:00 | admin | **not recommended** |
| C — Weekly game minutes | Saturday 09:00 | admin | **not recommended** |
| D — Bonus task nudge | daily 16:00 | student | allowed |

> **Important:** Crons B and C are tied to the game minutes calculation and week \
finalization logic. Changing their schedule may break the bonus accrual algorithm. \
Strongly advise the user not to reschedule these crons. \
If the user insists — warn explicitly about the risks and ask them to confirm knowingly.

---

## Step 3 — Create 4 crons

### Cron A — Homework reminders (Mon–Fri 17:00)

**Schedule:** `0 17 * * 1-5`

**What it does:**
1. Calls `learning_hub_get_pending_homework_reminders()` — returns a list of D-2 and D-1 \
reminders. Deduplication is built into the database.
2. If the list is empty — stop silently.
3. Sends each reminder to the student in a friendly tone. \
D-2: gentle heads-up. D-1: more urgent.
4. Calls `learning_hub_mark_homework_reminders_sent(\
d1_homework_ids=[...], d2_homework_ids=[...])`.

---

### Cron B — Unfinalized week reminder (Wednesday 12:00)

**Schedule:** `0 12 * * 3` ⚠️ do not reschedule

**What it does:**
1. Computes last Saturday's date (today minus 4 days).
2. Calls `learning_hub_get_week(week_key=<last Saturday YYYY-MM-DD>)`.
3. If the week is not found or `is_finalized=true` — stop silently.
4. If `is_finalized=false` — notifies the admin that the previous week is not closed yet. \
Asks them to report how many minutes the student actually played over the weekend, \
so the week can be finalized via `learning_hub_finalize_week`.

---

### Cron C — Weekly game minutes calculation (Saturday 09:00)

**Schedule:** `0 9 * * 6` ⚠️ do not reschedule

**What it does:**
1. Calls `learning_hub_calculate_weekly_minutes(\
new_week_key=<today's Saturday YYYY-MM-DD>)`.
2. If the response contains `auto_finalized_prev_week=true` — notifies the admin that \
the previous week was closed automatically (reason is in `auto_finalized_note`).
3. Sends the admin a brief summary of the new week: \
earned minutes, bonuses, carryover, total available.

---

### Cron D — Bonus task nudge (daily 16:00)

**Schedule:** `0 16 * * *`

**What it does:**
1. Calls `learning_hub_list_topic_reviews(status="pending")` — checks if there are topics \
available for bonus tasks.
2. If the list is empty — stop silently.
3. If topics exist — sends the student a short friendly invitation to earn extra game minutes. \
Does NOT reveal the topic yet. Does NOT create a BonusTask.

---

## Step 4 — Report to the user

After creating all 4 crons:
1. List them with name, schedule, and job ID.
2. Briefly explain what each one does.
3. Offer to adjust the schedule for crons A and D if the defaults don't work.

---

## Step 5 — Mark as installed

Call `{TOOL_SET_CONFIG}(key="{CFG_BASE_CRONS_INSTALLED}", value="true")`.

This flag ensures this tool is not triggered again in future sessions.
"""
