from learning_hub.tools.config_vars import CFG_ISSUES_LOG
from learning_hub.tools.tool_names import (
    TOOL_ADD_GRADE,
    TOOL_CREATE_TOPIC,
    TOOL_GET_CONFIG,
    TOOL_GET_GRADE_TO_MINUTES_MAP,
    TOOL_LIST_GRADES,
    TOOL_LIST_SUBJECTS,
    TOOL_LIST_TOPICS,
)

GRADE_MANUAL_INSTRUCTIONS = f"""\
# Manual grade entry

> Call this tool when an adult (parent, tutor) \
wants to add a grade manually — not via EduPage sync \
and not via bonus task evaluation.

## Who can add grades

Only an **adult** can add a grade — parent, tutor, \
or admin. \
The student **cannot** add grades for themselves. \
If the request comes from a student — **refuse**.

## When to activate

Request from an adult to add a grade:
- "give a 2 in math"
- "the student got a 1 in science"
- "grade for the test — 3"
- and any variations

---

## Step 1 — Parse the request

Extract from the message:

| What to determine | Examples |
|---|---|
| **Subject** | math, science, history, Czech… |
| **School** | CZ, UA (if clear from context) |
| **Grade** | number on the school's scale |
| **Date** | "today", "yesterday", "on Friday", specific date |
| **Topic** | "fractions", "verbs of motion" — optional |
| **Context** | what the grade is for: test, lesson, oral answer |

---

## Step 2 — Verify the grade scale

Learning Hub uses the **European 5-point scale** (1 = best, 5 = worst).

Current school scales are described in `USER.md` (section "Grade scales"). \
If the school's scale matches MCP — no conversion needed. \
If it doesn't — **convert** to European 1–5 before recording.

If in doubt — **ask** the user: \
"Is grade X on the 1–5 scale where 1 is the best?"

---

## Step 3 — Determine the subject (`subject_id`)

1. Call `{TOOL_LIST_SUBJECTS}` (with `school` filter if the school is known).
2. Find the matching subject by name.
3. If the subject is not found — ask the user.

---

## Step 4 — Determine the topic (`subject_topic_id`)

The topic matters: if the grade is poor (3/4/5), the system will create a TopicReview \
and generate bonus tasks on this topic for reinforcement.

1. If the user specified a topic — find or create it (see below).
2. If the user **did not specify** a topic — **ask**: \
"What topic is the grade for? This matters: the system will generate \
reinforcement tasks for topics with poor grades. \
If the topic is unknown — let me know, I'll record it without one."
3. If the user confirms no topic — leave it empty.

Finding/creating a topic:
1. Call `{TOOL_LIST_TOPICS}(subject_id=...)`.
2. Find a matching topic.
3. If none found — create: `{TOOL_CREATE_TOPIC}(subject_id=..., description=...)`.

---

## Step 5 — Determine the date

- If the user specified a date — use it.
- If not — **ask**: "What date is the grade for?"
- Format: ISO (YYYY-MM-DD). Timezone: Europe/Vienna.

---

## Step 6 — Check for duplicates

Call `{TOOL_LIST_GRADES}(subject_id=..., date_from=<date>, date_to=<date+1day>)`.

If a grade with the same value for the same subject already exists for that day — \
**warn**: "There is already such a grade for this day. Add another one?"

---

## Step 7 — Confirmation card

Show the user before recording:

```
Grade

Subject: <name>
School: <CZ/UA>
Grade: <value> (<verbal>)
Date: <date>
Topic: <topic or "not specified">
Minutes impact: <+N / -N / 0 min>
```

Get minutes impact from `{TOOL_GET_GRADE_TO_MINUTES_MAP}`. \
Wait for confirmation.

---

## Step 8 — Record the grade

```
{TOOL_ADD_GRADE}(
    subject_id=<id>,
    grade_value=<1-5>,
    date=<ISO>,
    subject_topic_id=<id>,  # if determined
)
```

Do not pass `bonus_task_id` or `homework_id` — this is a manual grade.

---

## Step 9 — Confirm the recording

After successful recording, inform the user:
- Grade recorded
- How it will affect the minutes balance

---

## Error handling

If `{TOOL_ADD_GRADE}` failed:
1. Inform the user: "Could not record the grade."
2. Get the log path: `{TOOL_GET_CONFIG}(key="{CFG_ISSUES_LOG}")`. \
Log the issue (date, context, error, status: open).

---

## Tools used

- `{TOOL_GET_CONFIG}` — get issue log path
- `{TOOL_LIST_SUBJECTS}` — find the subject
- `{TOOL_LIST_TOPICS}` — find the topic
- `{TOOL_CREATE_TOPIC}` — create a topic
- `{TOOL_LIST_GRADES}` — check for duplicates
- `{TOOL_ADD_GRADE}` — record the grade
- `{TOOL_GET_GRADE_TO_MINUTES_MAP}` — grade to minutes conversion table
"""
