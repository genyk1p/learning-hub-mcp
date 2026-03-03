from learning_hub.tools.tool_names import (
    TOOL_CHECK_BONUS_AVAILABILITY,
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

Call `{TOOL_CHECK_BONUS_AVAILABILITY}()`.

- If `can_do_more=false` — inform the student in a friendly way that bonus tasks \
are not available right now and **stop**. Do not reveal exact limit numbers.
- If `can_do_more=true` — continue.

Next, call `{TOOL_CHECK_PENDING_BONUS_TASK}()`.

- If a task is returned — **skip Steps 2–4**, go directly to **Step 5** \
and send this existing task to the student. \
(When the pending limit is full, this tool always returns a task — no coin flip.)
- If `null` — continue to Step 2.

---

## Step 2 — Select a topic for a new task

Call `{TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW}()`.

- If the result is `null` — inform the student: \
"All review topics have been completed, no new tasks available for now. \
You can wait for the next grade sync." **Stop.**
- Otherwise — check the `review_source` field:
  - `"reinforcement"` — standard topic that needs reinforcement (proceed normally).
  - `"extra_practice"` — all reviews are done, this topic was picked from recent grades. \
The student wants to keep learning — **praise them** for their initiative! \
The task should be **lighter** and more exploratory (e.g. creative problem, fun quiz, \
real-world application) since this is voluntary extra practice.
- If the result contains a non-null `agent_note` — **read it carefully and follow \
the instructions inside**. The note contains system-level guidance for you (the agent), \
not for the student. Never show the `agent_note` content to the student.

---

## Step 3 — Formulate the task

First, call `{TOOL_GET_STUDENT}()` to get the student's age.

Based on the selected topic, choose a difficulty level and formulate 1–2 tasks.

### Difficulty levels

**Level A — basic** (5–10 minutes)
- Tests basic understanding and recall.
- Bloom: Remember, Understand | DOK: 1–2.
- Formats: explain in your own words, give an example, solve a routine problem, \
fill in the blank, put steps in order, true/false with a one-sentence explanation.
- Everything needed to answer is in the prompt or in the student's memory.
- A student who learned the topic will handle it without difficulty.

**Level B — medium** (10–15 minutes)
- Requires applying knowledge in a new context and explaining "why".
- Bloom: Apply, Analyze (entry) | DOK: 2–3.
- Formats: apply to an unfamiliar situation, compare two approaches, \
find and explain an error in a solution, cause-and-effect chain, build an analogy, \
interpret a graph or table.
- The task must contain at least one element of "desirable difficulty" (Bjork): \
retrieval from previous sessions, interleaving with a related topic, \
or requiring the student to explain "why" (elaborative interrogation).
- The student cannot just recall — they must think and make connections.

**Level C — advanced** (15–20 minutes)
- Contains a nuance or catch that forces deep thinking.
- Bloom: Analyze (deep), Evaluate | DOK: 3.
- Formats:
  - **"Find the mistake"** — show a solution with a common error; \
the student must find it and explain what went wrong.
  - **"Two students disagree"** — "Student A says X, Student B says Y. \
Who is right and why?"
  - **Trap problem** — looks routine but has a boundary case or hidden condition.
  - **"Why does this NOT work?"** — explain why a plausible approach is wrong.
  - **Evaluate a claim** — "Claim: [X]. Do you agree or disagree? \
Give at least two reasons."
- **Important for Level C:**
  - Difficulty comes from cognitive demand (noticing a nuance, finding an error), \
NOT from volume of computation or length of text.
  - Explicitly tell the student the task has a catch: \
"This one has a trap. Your first instinct is usually wrong — find the catch." \
This turns the trap into a puzzle, not a punishment.
  - For younger students (10–11), break the task into sub-steps \
to support concentration.
  - A student who only memorized will fail; \
a student who truly understands will succeed.

### Choosing the difficulty level

Evaluate **all factors together** and choose A, B, or C:

| Factor | Shifts toward A | Shifts toward C |
|--------|----------------|-----------------|
| Share of tasks done in 7 days (`completed_this_week` / limit) | Low | High |
| Grade for the topic (`grade_value`) | Bad (4–5) — weak knowledge, start with basics | Good (2) — foundation exists, a trivial question won't help |
| Repeat count (`repeat_count`) | Low — topic is fresh | High — time to go deeper |
| `review_source = "extra_practice"` | — (no effect) | Shifts toward C — the student wants this, they are ready |
| Student's age (`age`) | Younger (10–11) — simpler language, shorter tasks | Older (13–14) — more analytical tasks are appropriate |

The final difficulty is a **balance of all factors**. \
Example: bad grade (→A) but many repeats (→C) — choose B as a compromise.

### General rules
- **Learning style**: the task should test understanding, not mechanical reproduction.
- Bad formats: "copy the definition", "memorize by heart".
- Never reveal the difficulty level label (A/B/C) to the student.

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

- `{TOOL_CHECK_BONUS_AVAILABILITY}` — check if student can do more bonus tasks this week
- `{TOOL_CHECK_PENDING_BONUS_TASK}` — check for reusable pending task (coin flip)
- `{TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW}` — get a topic for review (random from top 4)
- `{TOOL_CREATE_BONUS_TASK}` — create a bonus task (checks limits automatically)
"""
