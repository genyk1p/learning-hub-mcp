from learning_hub.tools.tool_names import (
    TOOL_CHECK_BONUS_LIMITS,
    TOOL_CHECK_PENDING_BONUS_TASK,
    TOOL_CREATE_BONUS_TASK,
    TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW,
    TOOL_GET_STUDENT,
)

BONUS_TASK_ASSIGNMENT_INSTRUCTIONS = f"""\
# Bonus task assignment to the student

> Call this tool when the student asks for a bonus task \
("give me a task", "I want to earn minutes", etc.).

## Step 1 — Check availability

Call `{TOOL_CHECK_BONUS_LIMITS}()`.

- If `can_create=false` — inform the student in a friendly way that bonus tasks \
are not available right now and **stop**. Do not reveal exact limit numbers.
- If `can_create=true` — continue.

Next, call `{TOOL_CHECK_PENDING_BONUS_TASK}()`.

- If a task is returned — **skip Steps 2–4**, go directly to **Step 5** \
and send this existing task to the student.
- If `null` — continue to Step 2.

---

## Step 2 — Select a topic for a new task

Call `{TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW}()`.

- If the result is `null` — inform the student: \
"All review topics have been completed, no new tasks available for now. \
You can wait for the next grade sync." **Stop.**
- Otherwise — use the returned topic.

---

## Step 3 — Formulate the task

Based on the selected TopicReview, formulate 1–2 tasks:

### Formulation rules:
- **Learning style**: the task should test understanding, not mechanical reproduction.
- Good formats: explain in your own words, solve a problem, give an example, \
find an error, compare two approaches.
- Bad formats: "copy the definition", "memorize by heart".
- Task difficulty should match the student's level and subject.
- **Adapt to the student's age** (from `{TOOL_GET_STUDENT}()` → `age`): \
simpler language and shorter tasks for younger students, \
more analytical and open-ended for older ones.
- The task should be completable in 10–20 minutes.

---

## Step 4 — Create a record in Learning Hub

Call `{TOOL_CREATE_BONUS_TASK}(subject_topic_id=<id>, task_description=<task text>)`.

- `subject_topic_id` — from the selected TopicReview.
- `task_description` — full task text as the student will see it.

If the tool returns an error (limit reached) — inform the student \
in a friendly way and **stop**. Do not reveal the exact limit numbers.

Remember the returned `task_id`.

---

## Step 5 — Send the task to the student

The message to the student **must** include:
- `task_id` in the format: **"Bonus task #<task_id>"**
- Task text
- Subject and topic

This is needed so that when submitting there is no ambiguity about which task the student is completing.

### Example message:

```
Bonus task #42

Subject: Mathematics
Topic: Fractions — addition and subtraction

Task: Explain in your own words why you need a common denominator \
when adding fractions. Give an example with two fractions that have different \
denominators, and show the solution step by step.
```

---

## Tools used

- `{TOOL_CHECK_BONUS_LIMITS}` — check if bonus tasks can be created (pending + weekly limits)
- `{TOOL_CHECK_PENDING_BONUS_TASK}` — check for reusable pending task (coin flip)
- `{TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW}` — get a topic for review (random from top 4)
- `{TOOL_CREATE_BONUS_TASK}` — create a bonus task (checks limits automatically)
"""
