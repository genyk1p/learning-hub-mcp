from learning_hub.tools.tool_names import (
    TOOL_GET_BOOK,
    TOOL_LIST_BOOKS,
    TOOL_LIST_HOMEWORKS,
    TOOL_LIST_SUBJECTS,
)

BOOK_LOOKUP_INSTRUCTIONS = f"""\
# Book Lookup — universal instruction for finding and delivering educational materials

> This instruction describes the algorithm for finding the right textbook (or a part of it) and delivering the result to the user.
> Applies to **any** request related to educational materials: "give me the textbook", "find the page", "I need material on the topic", "what's assigned for math — I need the textbook to do it", etc.

## When to activate

Any user request that implies obtaining educational material:
- "give me the math textbook"
- "I need the page with task 2"
- "show me lesson 5 on nature"
- "what's assigned for math — I need the textbook to do it"
- "send me material on the topic rational numbers"
- "I need homework from the textbook"
- and any variations

## Step 1 — Parse the request

Extract as much information as possible from the request:

| What to determine | Examples |
|---|---|
| **Subject** | math, nature, history, geography… |
| **Topic / lesson** | "lesson 5", "rational numbers", "paleozoic" |
| **Specific task** | "task 2", "homework for lesson 1" |
| **Page range** | "pages 3-4" |
| **Context** | homework, lesson preparation, topic review |

If the request only makes it clear that some textbook is needed, but not which one — proceed to step 2 with whatever information is available.

## Step 2 — Search for the book in Learning Hub

### 2.1 Search by subject (if the subject is known)

1. Call `{TOOL_LIST_SUBJECTS}` — find the `subject_id` for the subject.
2. Call `{TOOL_LIST_BOOKS}(subject_id=<id>)` — get the list of books for that subject.

### 2.2 Search across the entire library (if the subject is unclear)

1. Call `{TOOL_LIST_BOOKS}()` — get all registered books.
2. Filter by `title`, `description`, and `original_filename` — look for matches with the request (topic, lesson, keywords). The original filename often contains useful information about the book's content.

### 2.3 Refine using the book's summary file

Each book in Learning Hub may have a `summary_path` field — a path to a file with a book description that contains:
- brief description
- approximate table of contents (lessons, sections)
- key topics

**Read the summary files of candidate books** to determine which book contains the needed material. The table of contents and key topics are the main guide for selection.

## Step 3 — Decision tree

### Option A: Book found, pages are clear

It is known with certainty:
- which book is needed
- which pages / sections are needed (determined from the summary or from the request)

**→ Proceed directly to extraction and delivery (step 4).**

### Option B: Book found, but pages are unclear

The book is identified, but the exact pages cannot be determined (e.g., the user asks for "task 2", but the table of contents doesn't have that level of detail).

**→ Read the PDF** (path in the book's `original_path` field) fully or in parts to find the needed fragment. If found — proceed to step 4. If not found — proceed to option D.

### Option C: Multiple candidate books

Several books match the request and there is no certainty which one is needed.

**→ Ask the user**, listing the candidates:

```
Found several books that might match:
1. Mathematics grade 6 — lessons 1-6 (logical problems)
2. Mathematics grade 6 — lessons 7-9 (rational numbers)
Which one do you need?
```

### Option D: Book not found

There is no matching book in the library.

**→ Inform the user honestly:**

```
No textbooks found for [subject/topic] in the library.
Currently available books cover: [list subjects that have books].
If you need to add a textbook — place the PDF on the server and ask me to process it.
```

### Option E: Request is too vague

No subject, no topic, no specifics.

**→ Ask a clarifying question:**

```
Which subject do you need the textbook for? If you have a specific topic or lesson number — let me know, it will be faster to find.
```

## Step 4 — Extraction and delivery

When the book is identified and the needed topic/section is known, deliver **both text and PDF**. \
The PDF may contain images, diagrams, and illustrations that are not present in markdown.

### 4.1 Text from markdown chunks (if `contents_path` exists)

1. Get book details via `{TOOL_GET_BOOK}` — check if `contents_path` is set.
2. **Read `contents.md`** — find which chunk file (`part_XX.md`) covers the needed topic/pages.
3. **Read the chunk** — open the matching `part_XX.md` file.
4. **Find the relevant fragment** inside the chunk — the specific section, exercise, or topic the user asked for.
5. **Return the text directly** to the user as a message (markdown formatted).

If the needed material spans **multiple chunks** — read all relevant chunks and combine the text.

### 4.2 PDF extraction (always, when pages are known)

1. Get the path to the book file from the `original_path` field (via `{TOOL_GET_BOOK}`).
2. **+1 page buffer rule**: if extracting a fragment (not the whole book) — always include **+1 page before** the first target page and **+1 page after** the last target page (to avoid cutting off the beginning/end of a section, task, or illustration). If the target page is the first or last in the book, do not add a buffer on that side.
3. **Determine the needed pages** using one of these methods:
   - by page range (e.g., "pages 3–4")
   - by text/phrase (find which pages contain the phrase/heading)
   - by section/heading (find the start/end of the section and collect all pages in that section)
4. **Build a new PDF** from the expanded page range (target + buffer pages):
   - take only the identified pages from the original;
   - combine into a single new document (name format: `<slug>_extract_<topic>.pdf`).
5. **Send the PDF** to the user alongside the text.
6. **Add a brief explanation**: which book, which pages, why these specific pages (indicate both target and added "buffer" pages).

If the user needs the **entire book** — send the file at `original_path` without extraction.

## Step 5 — Homework context

If the request is related to homework:

1. Check current homework via `{TOOL_LIST_HOMEWORKS}(status="pending")`.
2. If the homework has a `book_id` — the book is already known. Call `{TOOL_GET_BOOK}(book_id)` and **skip step 2 entirely** — go straight to step 3/4.
3. If no `book_id` — extract hints from the homework description: subject, lesson, topic.
4. Use this information to search for the book (step 2).

Example: homework "Complete task 2 from lesson 5" → check `book_id` first; if set — use that book directly; if empty — search for a book by the homework's subject, lesson 5, task 2.

## Tools used

- `{TOOL_LIST_BOOKS}` — search books (filter by `subject_id`, `has_summary`)
- `{TOOL_GET_BOOK}` — get a book by ID (contains `original_path`, `summary_path`, `contents_path`, `original_filename`)
- `{TOOL_LIST_SUBJECTS}` — list of subjects for determining `subject_id`
- `{TOOL_LIST_HOMEWORKS}` — list of homework (for request context)
"""
