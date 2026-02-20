from learning_hub.tools.config_vars import CFG_ISSUES_LOG
from learning_hub.tools.tool_names import (
    TOOL_COMPLETE_HOMEWORK,
    TOOL_GET_BOOK,
    TOOL_GET_CONFIG,
    TOOL_LIST_FAMILY_MEMBERS,
    TOOL_LIST_HOMEWORKS,
    TOOL_LIST_SUBJECTS,
)

HOMEWORK_EVALUATION_INSTRUCTIONS = f"""\
# Homework evaluation

> Call this tool when it has been determined that the student is submitting homework \
(after routing via submission_routing). Works for any school.

## Important: homework grade is only a recommendation

The agent **does not assign the actual grade** for homework (does not call `add_grade`). \
The final grade is given by the teacher. The agent can only record \
a **recommended grade** via `{TOOL_COMPLETE_HOMEWORK}(recommended_grade=...)`.

This differs from bonus tasks, where the agent assigns the grade directly.

---

## Step 1 — Find the homework in Learning Hub

If `homework_id` is already known from routing — use it.

If not — call `{TOOL_LIST_HOMEWORKS}(status="pending")` and try to \
match by subject, description, deadline.

**If the homework could not be unambiguously matched** — evaluate the answer, \
but **do not write anything** to Learning Hub. Just give feedback to the student.

---

## Step 2 — Load assignment context from the book

If the homework has a `book_id` field filled in — the assignment is linked to a specific book. \
Use the book to better understand the assignment context **before evaluation**:

1. Call `{TOOL_GET_BOOK}(book_id=<id>)` — get the book data.
2. If the book has a `contents_path`:
   - Read the `contents.md` file — this is the book's chunk index.
   - By the homework description (topic, task number, page) find the needed chunk (`part_XX.md`).
   - Read the chunk — find the specific assignment/section.
3. If there is no `contents_path` — try reading the needed pages from `original_path` (PDF).
4. If the assignment could not be found in the book — evaluate the answer based on the homework description as-is.

Context from the book helps to:
- Understand what exactly was required in the assignment
- More accurately assess completeness and correctness of the answer
- Give more specific feedback

---

## Step 3 — Evaluate the answer

### 3.1 Standard evaluation (assignment can be graded)

Evaluate in **Socratic learning** style:
- Give feedback: what is correct, what is not, what to pay attention to.
- If there are errors — suggest corrections, explain why.
- Assign a **recommended grade** (1–5, European scale: 1 is best).

### 3.2 Assignment cannot be verified

There are cases where it is objectively impossible to verify completion:
- "Watch the video at this link" (no access to video content)
- "Listen to the audio recording" (no transcript)
- "Do the physical exercise"

In such cases:
1. Honestly tell the student that verification is not possible and **why**.
2. Ask for a brief confirmation from the student: what they did, what they understood \
(a short summary in their own words).
3. If the student confirms completion — proceed to step 4 \
(only if the homework was found in Learning Hub).
4. Get the log path via `{TOOL_GET_CONFIG}(key="{CFG_ISSUES_LOG}")` and log: which homework could not be verified \
and why (date, subject, homework_id if available, reason, status: open).

---

## Step 4 — Record the result

### "COMMIT BEFORE CONFIRM" RULE (mandatory)

**It is forbidden** to tell the student "homework submitted" or "all good" until successful recording in the system.

### 4.1 Conditions for recording

Record the result **only if** all conditions are met:
- Homework was found in Learning Hub (has `homework_id`)
- Recommended grade is **1, 2, or 3**

### 4.2 Write the result

Call `{TOOL_COMPLETE_HOMEWORK}(homework_id=<id>, recommended_grade=<1-3>)`.

This single call sets the recommended grade and marks the homework as completed.

### 4.3 If conditions are not met

- Homework not found in Learning Hub — do not write anything, just give feedback.
- Grade 4 or 5 — do not close the homework, suggest the student redo it.

---

## Step 5 — Confirm to the student

**Only after** successful recording (step 4.2) — inform the student:
- Homework accepted
- Recommended grade
- If there were remarks — a brief summary

---

## Step 6 — If the student refuses to redo

If grade is 4–5 and the student says "I won't redo it" or "it's fine as is":

1. Do not argue, do not pressure.
2. Determine the responsible tutor from the subject's `tutor_id` field:
   - Call `{TOOL_LIST_SUBJECTS}()` and find the subject for this homework.
   - If `tutor_id` is set → that FamilyMember is responsible. \
Use `{TOOL_LIST_FAMILY_MEMBERS}()` to get their name and default gateway.
   - If `tutor_id` is null → forward to the admin (is_admin=true).
3. Forward to the responsible person:
   - The student's solution (text/photo)
   - The recommended grade
   - A brief explanation of what is wrong
4. If the subject is unclear — clarify with the student.

---

## Error handling

If the call to `{TOOL_COMPLETE_HOMEWORK}` **failed**:

1. Write to the student in a neutral tone: \
"The content looks good, but could not record it in the system."

2. Include in the message a short log for the adult (what went wrong).

3. Get the log path via `{TOOL_GET_CONFIG}(key="{CFG_ISSUES_LOG}")` and log (date, context, error, status: open).

4. **Do not confirm as recorded** until a successful call.

---

## Tools used

- `{TOOL_GET_CONFIG}` — read config values (issue log path)
- `{TOOL_LIST_HOMEWORKS}` — find the homework
- `{TOOL_GET_BOOK}` — load book data for assignment context
- `{TOOL_COMPLETE_HOMEWORK}` — set recommended grade and mark as completed
- `{TOOL_LIST_SUBJECTS}` — get subject with tutor_id
- `{TOOL_LIST_FAMILY_MEMBERS}` — get tutor/admin contact info
"""
