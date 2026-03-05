"""Base cron jobs setup instruction — guides agent through creating base crons."""

from learning_hub.tools.config_vars import CFG_BASE_CRONS_INSTALLED
from learning_hub.tools.tool_names import TOOL_CLOSE_OVERDUE_HOMEWORKS, TOOL_SET_CONFIG

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
- Reminder to the admin if they forgot to record played time for the week
- Weekly balance report to the student every Saturday
- Daily nudge encouraging the student to do a bonus task
- Nightly auto-close of overdue homeworks

These 5 crons are required regardless of whether a sync provider (EduPage, etc.)
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

Before creating, show the user all 5 crons with their default schedules and ask for confirmation.

| Cron | Schedule | Recipient | Reschedule? |
|------|----------|-----------|-------------|
| A — Homework reminders | Mon–Fri 17:00 | student | allowed |
| B — Unrecorded play reminder | Wednesday 12:00 | admin | allowed |
| C — Saturday balance report | Saturday 09:00 | student | allowed |
| D — Bonus task nudge | daily 16:00 | student | allowed |
| E — Close overdue homeworks | daily 01:00 | none (silent) | allowed |

---

## Step 3 — Create 5 crons

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

### Cron B — Unrecorded play reminder (Wednesday 12:00)

**Schedule:** `0 12 * * 3`

**What it does:**
1. Take the current date (when the cron fires) and call \
`learning_hub_list_transactions(date_from=<7 days ago YYYY-MM-DD>, type="played")`.
2. If there is at least one PLAYED transaction in the last 7 days — stop silently.
3. If there are no PLAYED transactions in the last 7 days — notify the admin. To compose \
the message, first check the full history:
   a. Call `learning_hub_list_transactions(type="played")` (no date filter).
   b. **If there is at least one PLAYED transaction ever** — find the most recent one \
and tell the admin: "No game time has been recorded in the last week. \
The last time you recorded played time was on [date]: [N] minutes. \
If the student has played since then, please record it via \
`learning_hub_add_played_minutes(minutes=<N>)`."
   c. **If there are no PLAYED transactions at all** — tell the admin: \
"You have never recorded how much the student played. \
When the student plays games, you should record the minutes spent — \
this deducts them from the balance and keeps it accurate. \
Use `learning_hub_add_played_minutes(minutes=<N>)` after each gaming session \
or as a daily/weekly total."

---

### Cron C — Saturday balance report (Saturday 09:00)

**Schedule:** `0 9 * * 6`

**What it does:**
1. Gets the current balance: `learning_hub_get_balance()`.
2. Gets this week's transactions: `learning_hub_list_transactions(\
date_from=<last Saturday YYYY-MM-DD>)`.
3. Sends the student a friendly weekly summary via their gateway: \
what was earned, what was spent, current balance.

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

### Cron E — Close overdue homeworks (daily 01:00)

**Schedule:** `0 1 * * *`

**What it does:**
1. Calls `{TOOL_CLOSE_OVERDUE_HOMEWORKS}()` — finds all homeworks past their deadline \
and marks them as overdue, applying penalty minutes from the config.
2. This cron runs silently — no notifications are sent. The penalty transactions \
are recorded automatically.

---

## Step 4 — Report to the user

After creating all 5 crons:
1. List them with name, schedule, and job ID.
2. Briefly explain what each one does.
3. Offer to adjust the schedule if the defaults don't work.

---

## Step 5 — Mark as installed

Call `{TOOL_SET_CONFIG}(key="{CFG_BASE_CRONS_INSTALLED}", value="true")`.

This flag ensures this tool is not triggered again in future sessions.
"""
