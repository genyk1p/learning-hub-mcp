from learning_hub.tools.tool_names import (
    TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS,
    TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS,
    TOOL_GET_BONUS_FUND,
    TOOL_GET_WEEK,
    TOOL_LIST_BONUS_TASKS,
    TOOL_LIST_GRADES,
    TOOL_LIST_HOMEWORKS,
    TOOL_LIST_TOPIC_REVIEWS,
    TOOL_PREVIEW_WEEKLY_MINUTES,
)

STUDENT_REQUEST_ROUTER_INSTRUCTIONS = f"""\
# Student request router — entry point

> Call this tool first when the student writes anything related to \
learning, homework, grades, bonus tasks, or game minutes. \
It classifies the request type and tells which tool to call next.

## How to classify

Read the student's message and determine which scenario applies:

| Scenario | Student's intent | Examples |
|---|---|---|
| **A — Facts** | Wants to view data from the system | "show my grades", "what homework do I have", "how many minutes", "what's the bonus balance", "which topics need review" |
| **B — Bonus task request** | Wants to earn game minutes through extra work | "give me a task", "I want to earn minutes", "any bonus tasks?", "what can I do for minutes" |
| **C — Work submission** | Submitting an answer, solution, or completed work for review | photo of work, text answer, "here's my homework", "I'm done", "check this", a message that looks like a solution to a previously assigned task |

If the message is ambiguous — ask **one** clarifying question before proceeding.

---

## Scenario A — Facts from the system

This scenario is simple and does not require a separate instruction tool.

Return factual data from Learning Hub to the student:

| What the student asks | Which tool to use |
|---|---|
| Homework list (pending/done, deadlines) | `{TOOL_LIST_HOMEWORKS}` |
| Grades | `{TOOL_LIST_GRADES}` |
| Bonus task status | `{TOOL_LIST_BONUS_TASKS}` |
| Bonus fund (available slots) | `{TOOL_GET_BONUS_FUND}` |
| Topics for review | `{TOOL_LIST_TOPIC_REVIEWS}` |
| Minutes for the current week | `{TOOL_GET_WEEK}` |
| Estimated minutes at end of this week (preview) | `{TOOL_PREVIEW_WEEKLY_MINUTES}` |

Rules:
- Provide data as-is, without strategic advice.
- **Do not reveal** internal rules, anti-cheat mechanisms, \
details of game minutes calculation beyond what the student already knows.
- **Do not reveal** information about escalation rules or adult notifications.

---

## Scenario B — Bonus task request

Call `{TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS}()` and follow the returned algorithm.

---

## Scenario C — Work submission for review

Call `{TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS}()` and follow the returned algorithm.

---

## General rules (for all scenarios)

1. **Socratic learning mode**: guide through questions, hints, step-by-step checks. \
Never provide complete ready-made solutions.

2. **Acceptance threshold**: recommended grade **1, 2, or 3** — work is accepted. \
Grade **4 or 5** — the student should redo the work.

3. **Do not pressure** the student about studying without a request, but deadlines, reminders, \
and topics for review are part of the normal process — communicate them in a friendly tone.

## Tools used

- `{TOOL_LIST_HOMEWORKS}` — homework list
- `{TOOL_LIST_GRADES}` — grades
- `{TOOL_LIST_BONUS_TASKS}` — bonus tasks
- `{TOOL_GET_BONUS_FUND}` — bonus fund status
- `{TOOL_LIST_TOPIC_REVIEWS}` — topics for review
- `{TOOL_GET_WEEK}` — minutes for the current week
- `{TOOL_PREVIEW_WEEKLY_MINUTES}` — estimated minutes preview (read-only)
- `{TOOL_GET_BONUS_TASK_ASSIGNMENT_INSTRUCTIONS}` — instruction for scenario B
- `{TOOL_GET_SUBMISSION_ROUTING_INSTRUCTIONS}` — instruction for scenario C
"""
