"""Grade escalation instruction — notify responsible adults about bad grades."""

from learning_hub.tools.config_vars import CFG_FAMILY_LANGUAGE
from learning_hub.tools.tool_names import (
    TOOL_GET_CONFIG,
    TOOL_GET_GRADES_PENDING_ESCALATION,
    TOOL_LIST_FAMILY_MEMBERS,
    TOOL_LIST_SUBJECTS,
    TOOL_MARK_GRADES_ESCALATED,
)

GRADE_ESCALATION_INSTRUCTIONS = f"""\
# Grade escalation

> Call this tool to run grade escalation — notify responsible adults \
about bad grades (3, 4, 5). Triggered after automatic grade sync \
(e.g. EduPage sync), typically by a daily cron job. \
Do NOT run after manual grade entry — the person who entered it \
already knows about the grade.

---

## Step 1 — Get grades pending escalation

Call `{TOOL_GET_GRADES_PENDING_ESCALATION}(threshold=3)`.

Returns grades with value 3, 4, or 5 where `escalated_at IS NULL`. \
Each grade includes: grade_id, grade_value, date, subject_id, \
subject_name, subject_name_ru, school, subject_topic_description.

**If the list is empty** — nothing to escalate. Stop here.

---

## Step 2 — Determine recipients

For each grade, determine who to notify:

1. Call `{TOOL_LIST_SUBJECTS}()` — get subjects with `tutor_id`.
2. Call `{TOOL_LIST_FAMILY_MEMBERS}()` — get all family members with gateways.

**Routing rule per grade:**
- Find the subject by `subject_id` from the grade.
- If the subject has `tutor_id` — the tutor is the recipient.
- If `tutor_id` is null — the recipient is the admin (`is_admin=true`).
- If no admin found — log an error and skip these grades.

---

## Step 3 — Group and compose messages

Group grades by recipient — **one message per person** with all their grades.

Get the family language: \
`{TOOL_GET_CONFIG}(key="{CFG_FAMILY_LANGUAGE}")`.

For each recipient, compose a message in the family language:
- Greeting by name.
- For each grade:
  - Subject name (prefer `subject_name_ru` if available, otherwise `subject_name`).
  - Grade value.
  - Date.
  - Topic description (if available; otherwise omit).
- Keep it brief and factual. No drama, no judgment.

---

## Step 4 — Send messages

Send each message to the recipient's gateway. \
Use the first available gateway from their profile.

**If sending fails** for a recipient — do not mark their grades as escalated. \
Continue with other recipients.

---

## Step 5 — Mark grades as escalated

After successful send, call \
`{TOOL_MARK_GRADES_ESCALATED}(grade_ids=[...])` \
with the IDs of grades whose recipient was successfully notified.

**Only mark grades that were actually sent.** \
If some sends failed — those grades remain pending for the next run.

---

## Tools used

- `{TOOL_GET_GRADES_PENDING_ESCALATION}` — get grades needing escalation
- `{TOOL_LIST_SUBJECTS}` — get subjects with tutor_id
- `{TOOL_LIST_FAMILY_MEMBERS}` — get family members with gateways
- `{TOOL_GET_CONFIG}` — get family language
- `{TOOL_MARK_GRADES_ESCALATED}` — mark grades as escalated after notification
"""
