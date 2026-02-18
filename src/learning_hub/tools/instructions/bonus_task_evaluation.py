from learning_hub.tools.config_vars import CFG_ISSUES_LOG, CFG_TOPIC_REVIEW_THRESHOLDS
from learning_hub.tools.tool_names import (
    TOOL_ADD_GRADE,
    TOOL_APPLY_BONUS_TASK_RESULT,
    TOOL_GET_BONUS_TASK,
    TOOL_GET_CONFIG,
    TOOL_GET_PENDING_REVIEWS_FOR_TOPIC,
    TOOL_INCREMENT_TOPIC_REPEAT_COUNT,
    TOOL_MARK_TOPIC_REINFORCED,
)

BONUS_TASK_EVALUATION_INSTRUCTIONS = f"""\
# Bonus task evaluation

> Call this tool when it has been determined that the student is submitting a bonus task \
(after routing via submission_routing).

## Step 1 — Load the task

Call `{TOOL_GET_BONUS_TASK}(task_id=<id>)`.

Check:
- Task status = `pending`. If the task is already `completed` or `cancelled` — \
inform the student and **stop**.
- Task description (`task_description`) — to understand what exactly needed to be done.

---

## Step 2 — Evaluate the student's answer

Evaluate in **Socratic learning** style:

### Evaluation criteria:
- **Topic understanding**: the student demonstrates understanding, not mechanical copying.
- **Completeness**: the answer covers what was assigned.
- **Correctness**: factual errors, logical errors.

### Grading scale (1–5, European):
- **1** — excellent, full understanding
- **2** — good, minor inaccuracies
- **3** — satisfactory, some gaps but the essence is understood
- **4** — poor, serious errors
- **5** — not completed / complete lack of understanding

### If the answer is insufficient (grade 4–5):
- Give feedback: what exactly is wrong, what to pay attention to.
- Suggest trying again.
- **Do not close the task.** The student can redo and resubmit.
- **Stop** (waiting for a retry).

### If the answer is acceptable (grade 1–3):
- Give brief feedback (what's good, what can be improved).
- Proceed to step 3.

---

## Step 3 — Record the result in Learning Hub

### "COMMIT BEFORE CONFIRM" RULE (mandatory)

**It is forbidden** to tell the student "task accepted", "grade recorded", \
"task closed" until the steps below are successfully completed.

### 3.1 Close the bonus task and update TopicReview

Call `{TOOL_APPLY_BONUS_TASK_RESULT}(task_id=<id>)`.

This tool:
- Marks the BonusTask as `completed`
- Deducts a slot from the bonus fund
- Automatically increments `repeat_count` on pending TopicReview for the same topic

### 3.2 Record the grade

Call `{TOOL_ADD_GRADE}(subject_id=<id>, grade_value=<1-3>, date=<ISO>, bonus_task_id=<id>)`.

- `subject_id` — from the BonusTask (via topic -> subject).
- `grade_value` — your recommended grade (1, 2, or 3).
- `date` — current date.
- `bonus_task_id` — task id.

### 3.3 Check TopicReview closure

Call `{TOOL_GET_PENDING_REVIEWS_FOR_TOPIC}(subject_topic_id=<id>)`.

For each pending review, check whether the repetition threshold has been reached.

Get the threshold map: call `{TOOL_GET_CONFIG}(key="{CFG_TOPIC_REVIEW_THRESHOLDS}")`.
The value is a JSON map: grade_value → required_repetitions (e.g. {{"2":1,"3":2,"4":3,"5":3}}).

If `repeat_count >= required repetitions for that grade` — \
call `{TOOL_MARK_TOPIC_REINFORCED}(review_id=<id>)`.

---

## Step 4 — Confirm the result to the student

**Only after** successful completion of step 3 — inform the student:
- Task accepted
- Grade (which one)
- If TopicReview was closed — "topic has been reinforced"

---

## Error handling

If the call to `{TOOL_APPLY_BONUS_TASK_RESULT}` or `{TOOL_ADD_GRADE}` **failed**:

1. Write to the student in a neutral tone: \
"I've checked everything, the content is fine, but **could not record it in the system**."

2. **Include in the message** a short log for the adult: \
what exactly went wrong (tool error / task_id not found / etc.). \
The student should be able to forward this message to an adult.

3. Get the log path: `{TOOL_GET_CONFIG}(key="{CFG_ISSUES_LOG}")`. \
Log the issue there (date, context, error, status: open).

4. **Do not confirm the result as recorded** until a successful call.

---

## Tools used

- `{TOOL_GET_CONFIG}` — read config values (thresholds, issue log path)
- `{TOOL_GET_BONUS_TASK}` — load the task
- `{TOOL_APPLY_BONUS_TASK_RESULT}` — close the task + update TopicReview
- `{TOOL_ADD_GRADE}` — record the grade
- `{TOOL_GET_PENDING_REVIEWS_FOR_TOPIC}` — check TopicReview status
- `{TOOL_INCREMENT_TOPIC_REPEAT_COUNT}` — increment repetition counter (if needed manually)
- `{TOOL_MARK_TOPIC_REINFORCED}` — close TopicReview
"""
