from learning_hub.tools.tool_names import (
    TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS,
    TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS,
    TOOL_GET_LATEST_BONUS_TASK,
    TOOL_LIST_BONUS_TASKS,
    TOOL_LIST_HOMEWORKS,
)

SUBMISSION_ROUTING_INSTRUCTIONS = f"""\
# Submission routing — determining the work type

> Call this tool when the student has submitted an answer, solution, or completed work \
for review, and you need to determine: is this a bonus task or homework (and which school).

## Main rule

**Until you have determined the work type — do not write or close anything in Learning Hub.** \
No `complete_homework`, `apply_bonus_task_result`, etc. until full classification.

---

## Step 1 — Check conversation context

If there is no conversation context with the student for the last ~24 hours — \
first pull the message history for the past day to understand what was discussed.

Look for:
- Was a bonus task assigned (with `task_id`)?
- Was a specific homework discussed?
- Was a subject or school mentioned?

---

## Step 2 — Check pending BonusTasks

Call `{TOOL_GET_LATEST_BONUS_TASK}(status="pending")` \
or `{TOOL_LIST_BONUS_TASKS}(status="pending")`.

Signs that the student is submitting a bonus task:
- The message mentions a `task_id` (e.g., "task #42").
- The answer content matches the description of a pending BonusTask.
- A bonus task was assigned to the student in the recent conversation.

If the match is unambiguous → **this is a BonusTask**. Proceed to step 4.

---

## Step 3 — Check pending Homeworks

Call `{TOOL_LIST_HOMEWORKS}(status="pending")`.

Signs that the student is submitting homework:
- The answer content matches the description of a pending homework.
- The subject from the message matches the homework's subject.
- The homework deadline is approaching (the student is hurrying to submit).

If the match is unambiguous → **this is homework**. Determine the school from the `school` field \
of the related subject and proceed to step 4.

---

## Step 3.1 — Could not determine automatically

If neither a BonusTask nor homework matched unambiguously — \
ask the student 1–2 clarifying questions:

**Question 1** (always): "Is this a bonus task for minutes or homework?"

**Question 2** (if needed): show a short list of active assignments and ask \
which one the student is submitting. For example:

```
You currently have open:
1. Bonus task #42 — Fractions (Mathematics CZ)
2. Homework: Czech language — exercise 5, p. 38 (deadline: tomorrow)
3. Homework: Mathematics UA — problem 12 (deadline: Friday)

Which one are you submitting?
```

---

## Step 4 — Call the appropriate tool

| Work type | Which tool to call |
|---|---|
| **BonusTask** | `{TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS}()` |
| **Homework** (any school) | `{TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS}()` |

Pass to the next tool's context:
- Work type (bonus / homework)
- Assignment ID (`task_id` or `homework_id`)
- School (if homework)
- The student's answer itself

---

## Tools used

- `{TOOL_GET_LATEST_BONUS_TASK}` — latest bonus task
- `{TOOL_LIST_BONUS_TASKS}` — list of bonus tasks
- `{TOOL_LIST_HOMEWORKS}` — list of homeworks
- `{TOOL_GET_BONUS_TASK_EVALUATION_INSTRUCTIONS}` — instruction for bonus task evaluation
- `{TOOL_GET_HOMEWORK_EVALUATION_INSTRUCTIONS}` — instruction for homework evaluation
"""
