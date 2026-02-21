from learning_hub.tools.tool_names import (
    TOOL_CREATE_HOMEWORK,
    TOOL_CREATE_TOPIC,
    TOOL_GET_BOOK,
    TOOL_GET_STUDENT,
    TOOL_LIST_BOOKS,
    TOOL_LIST_HOMEWORKS,
    TOOL_LIST_SCHOOLS,
    TOOL_LIST_SUBJECTS,
    TOOL_LIST_TOPICS,
    TOOL_UPDATE_SUBJECT,
)

HOMEWORK_MANUAL_INSTRUCTIONS = f"""\
# Manual homework creation

> This instruction describes the algorithm for adding homework manually — \
when the assignment comes not from EduPage but from a parent or another source.

## Who can add homework

Homework is accepted from **any source except the child themselves**. \
The child cannot create homework assignments for themselves. \
If a homework creation request comes from the child — **refuse**.

## When to activate

Any request from a user (not the child) to add homework manually:
- "write down math homework"
- "they assigned exercise 5 on page 42"
- "Czech homework — learn words by Friday"
- "add a nature studies assignment"
- and any variations

---

## Step 1 — Parse the request

Extract as much information as possible from the user's message:

| What to determine | Examples |
|---|---|
| **Subject** | math, nature studies, history, Czech language… |
| **School** | school ID or name (if known from context) |
| **Task description** | "exercise 5 on p. 42", "learn paragraph 3" |
| **Topic** | "fractions", "verbs of motion", "paleozoic" |
| **Deadline** | "by Friday", "for tomorrow", "before Feb 15" |
| **Textbook reference** | page, exercise number, textbook name |

---

## Step 2 — Determine the school and subject (`subject_id`)

### 2.1 Determine the school

1. Call `{TOOL_LIST_SCHOOLS}(is_active=true)` — get the list of active schools.
2. If there is **only one** active school — use it (no need to ask).
3. If there are **multiple** active schools — try to infer from context \
(subject name, language hints, prior conversation). If still unclear — ask the user \
which school the homework belongs to.

### 2.2 Find the subject

1. Call `{TOOL_LIST_SUBJECTS}(school_id=<school_id>)` — get subjects for the determined school.
2. Find the matching subject by name.
3. If the subject is not found — ask the user, clarify the name. \
Also reconsider whether the correct school was determined in step 2.1.

---

## Step 3 — Determine the topic (`subject_topic_id`)

1. Call `{TOOL_LIST_TOPICS}(subject_id=...)` — get the list of topics for the subject.
2. Find a topic that matches the assignment.
3. If no matching topic exists — create a new one via `{TOOL_CREATE_TOPIC}(subject_id=..., description=...)`.

---

## Step 4 — Book (`book_id`)

### 4.1 Get the current textbook for the subject

Each subject (Subject) has a `current_book_id` field — the current textbook. \
This is the primary source for linking a book to the homework assignment.

### 4.2 Verification — only if the assignment references a textbook

Verification should be done **only if** the assignment has an explicit reference to a textbook: \
page number, exercise number, "from the textbook", etc.

If the assignment is general ("learn words", "prepare a report") — \
book verification is not needed, `book_id` can be omitted.

### 4.3 Algorithm for verifying the assignment in the textbook

1. Call `{TOOL_GET_BOOK}(book_id=current_book_id)` — get the book data.
2. If the book has a `contents_path`:
   - read the `contents_path` file (`contents.md`) — this is the chunk index;
   - find which chunk (`part_XX.md`) covers the needed pages/topic;
   - read that chunk;
   - find the exercise/assignment from the homework in it.
3. If there is no `contents_path` — skip chunk verification, \
rely on the PDF (read the needed pages from `original_path`).

### 4.4 Book mismatch

If the assignment clearly references a textbook, but the linked book (`current_book_id`) \
does not contain that assignment (missing page, missing exercise):

1. Inform the user about the mismatch.
2. The user may have forgotten to re-link the textbook.
3. Show the list of available books for the subject via `{TOOL_LIST_BOOKS}(subject_id=...)`.
4. If re-linking is needed — call `{TOOL_UPDATE_SUBJECT}(subject_id=..., current_book_id=<new_id>)`.
5. After re-linking, repeat the assignment verification in the new book.

---

## Step 5 — Deadline

If the user **did not specify** a deadline — **always ask for it**.

---

## Step 6 — Clarification

If at any of the previous steps something is unclear or there are doubts — \
**ask the user** before proceeding. \
Do not guess, do not assume — it is better to clarify.

---

## Step 7 — Assignment preview card

Before registration, show the user a full assignment card for confirmation:

```
Homework assignment

Subject: <subject name>
Topic: <topic>
Assignment: <description>
Deadline: <date>
Textbook: <book title> (if linked)
```

If the assignment is from a textbook — additionally attach:
- **PDF pages** from `original_path` (extract the needed pages);
- **exercise text** from text chunks — so the user can read \
the assignment and confirm it is exactly what is needed.

### Correction

If the user wants to change something — understand what exactly, make corrections, \
show the updated card. Repeat until the user confirms.

---

## Step 8 — Register the assignment

After user confirmation, call:

```
{TOOL_CREATE_HOMEWORK}(
    subject_id=<subject id>,
    description=<assignment description>,
    subject_topic_id=<topic id>,       # if determined
    book_id=<current_book_id>,         # if assignment is from a textbook
    deadline_at=<deadline ISO format>,  # if specified
)
```

---

## Step 9 — Notify the child

After successful registration, send the assignment to the child \
via the standard communication method.

The message should be **adapted to the student's age** \
(from `{TOOL_GET_STUDENT}()` → `age`): \
clear, concise, and easy to understand for their developmental stage.

The message should include:
- subject
- what needs to be done
- deadline
- pages/exercises from the textbook (if any)

---

## Tools used

- `{TOOL_LIST_SCHOOLS}` — get active schools to determine the school
- `{TOOL_LIST_SUBJECTS}` — find the subject
- `{TOOL_LIST_TOPICS}` — find the subject topic
- `{TOOL_CREATE_TOPIC}` — create a new topic
- `{TOOL_GET_BOOK}` — get book data (file paths, `contents_path`)
- `{TOOL_LIST_BOOKS}` — list of books for the subject
- `{TOOL_UPDATE_SUBJECT}` — re-link the current textbook
- `{TOOL_CREATE_HOMEWORK}` — register the assignment
- `{TOOL_LIST_HOMEWORKS}` — check existing assignments (for deduplication)
"""
