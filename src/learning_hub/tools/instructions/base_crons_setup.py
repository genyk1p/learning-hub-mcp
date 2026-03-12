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

## Step 2 — Detect server timezone

All cron schedules must use the **server's local timezone** so that notifications arrive \
at the correct local time for the family.

Run `cat /etc/timezone` (or `timedatectl show -p Timezone --value`) to get the server timezone. \
Use the resulting IANA timezone identifier (e.g. `Europe/Vienna`, `America/New_York`) as \
the `tz` parameter when creating every cron job below.

Also use the server's current local time (`date`) to verify the timezone looks correct \
(e.g. if it's evening in Europe, the time should reflect that).

If the server timezone is `Etc/UTC` or `UTC` — ask the user what timezone the family lives in \
and use that instead.

Store the resolved timezone — you will use it for **all** cron jobs in step 4.

---

## Step 3 — Show schedule and get confirmation

Before creating, show the user all 5 crons with their default schedules \
(**in the server's local timezone from step 2**) and ask for confirmation.

| Cron | Schedule (local time) | Recipient | Reschedule? |
|------|----------------------|-----------|-------------|
| A — Homework reminders | Mon–Fri 17:00 | student | allowed |
| B — Unrecorded play reminder | Wednesday 12:00 | admin | allowed |
| C — Saturday balance report | Saturday 09:00 | student | allowed |
| D — Bonus task nudge | daily 16:00 | student | allowed |
| E — Close overdue homeworks | daily 01:00 | none (silent) | allowed |

---

## Step 4 — Create 5 crons via `openclaw cron add`

**How to create crons in OpenClaw:**

Use the CLI command `openclaw cron add`. This is the ONLY correct way to create crons. \
Do NOT write to `jobs.json` directly. Do NOT use system `crontab`. Do NOT create documentation \
files instead of actual crons.

**Mandatory flags for EVERY cron:**
- `--tz <TIMEZONE>` — timezone from step 2. Never omit this.
- `--session isolated` — all crons MUST run in isolated sessions. \
This prevents cron output from leaking into active user chats \
(e.g. sending an admin notification into the student's Telegram conversation).
- `--message "<text>"` — the instruction the agent will execute when the cron fires.
- `--timeout-seconds 180` — timeout for the agent job (3 minutes is enough for most crons).

**Template:**
```
openclaw cron add \\
  --name "<NAME>" \\
  --cron "<CRON_EXPR>" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "<INSTRUCTION>"
```

Before running the commands, substitute these placeholders with real values from step 1:
- `<TIMEZONE>` — IANA timezone from step 2 (e.g. `Europe/Prague`)
- `<STUDENT_NAME>` — student's name from `list_family_members()`
- `<STUDENT_TG>` — student's gateway channel_uid (Telegram ID)
- `<ADMIN_NAME>` — admin's name
- `<ADMIN_TG>` — admin's gateway channel_uid (Telegram ID)

---

### Cron A — Homework reminders (Mon–Fri 17:00)

```
openclaw cron add \\
  --name "LH: Homework Reminders" \\
  --cron "0 17 * * 1-5" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "Call learning_hub_get_pending_homework_reminders(). \
If the list is empty — do nothing. \
If not empty — send each reminder to <STUDENT_NAME> via Telegram (<STUDENT_TG>). \
D-2: gentle heads-up. D-1: more urgent tone. \
Then call learning_hub_mark_homework_reminders_sent(d1_homework_ids=[...], d2_homework_ids=[...])."
```

---

### Cron B — Unrecorded play reminder (Wednesday 12:00)

```
openclaw cron add \\
  --name "LH: Play Reminder" \\
  --cron "0 12 * * 3" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "Call learning_hub_list_transactions(date_from=<7 days ago YYYY-MM-DD>, type='played'). \
If there is at least one transaction — do nothing. \
If none — call learning_hub_list_transactions(type='played') without date filter. \
If there is at least one ever — find the most recent and tell <ADMIN_NAME> via Telegram (<ADMIN_TG>): \
'No game time recorded in the last week. Last recorded: [date], [N] minutes.' \
If none ever — tell admin: 'You have never recorded played time. \
Use learning_hub_add_played_minutes(minutes=N) after gaming sessions.'"
```

---

### Cron C — Saturday balance report (Saturday 09:00)

```
openclaw cron add \\
  --name "LH: Weekly Balance Report" \\
  --cron "0 9 * * 6" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "Get balance via learning_hub_get_balance(). \
Get this week's transactions via learning_hub_list_transactions(date_from=<last Saturday YYYY-MM-DD>). \
Send <STUDENT_NAME> via Telegram (<STUDENT_TG>) a friendly weekly summary: \
what was earned, what was spent, current balance."
```

---

### Cron D — Bonus task nudge (daily 16:00)

```
openclaw cron add \\
  --name "LH: Bonus Task Nudge" \\
  --cron "0 16 * * *" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "Call learning_hub_list_topic_reviews(status='pending'). \
If list is empty — do nothing. \
If topics exist — send <STUDENT_NAME> via Telegram (<STUDENT_TG>) a short friendly \
invitation to earn game minutes via a bonus task. Do NOT reveal the topic. Do NOT create a BonusTask."
```

---

### Cron E — Close overdue homeworks (daily 01:00)

```
openclaw cron add \\
  --name "LH: Close Overdue Homeworks" \\
  --cron "0 1 * * *" \\
  --tz <TIMEZONE> \\
  --session isolated \\
  --timeout-seconds 180 \\
  --message "Call learning_hub_close_overdue_homeworks(). This is a silent background task — do not send any notifications."
```

---

### Verify crons were created

After running all 5 commands, verify:
```
openclaw cron list
```
Must show 5 crons, all enabled. If any are missing — re-run the failed command.

---

## Step 5 — Report to the user

After creating all 5 crons:
1. List them with name, schedule, and job ID.
2. Briefly explain what each one does.
3. Offer to adjust the schedule if the defaults don't work.

---

## Step 6 — Mark as installed

Call `{TOOL_SET_CONFIG}(key="{CFG_BASE_CRONS_INSTALLED}", value="true")`.

This flag ensures this tool is not triggered again in future sessions.
"""
