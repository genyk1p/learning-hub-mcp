"""Instruction tools for MCP server.

Returns workflow instructions that the agent should follow
when performing book-related operations.
"""

from mcp.server.fastmcp import FastMCP


BOOK_LOOKUP_INSTRUCTIONS = """\
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

1. Call `list_subjects` — find the `subject_id` for the subject.
2. Call `list_books(subject_id=<id>)` — get the list of books for that subject.

### 2.2 Search across the entire library (if the subject is unclear)

1. Call `list_books()` — get all registered books.
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

When the book is identified and the needed pages are known:

1. Get the path to the book file from the `original_path` field (via `get_book`).
2. **+1 page buffer rule**: if extracting a fragment (not the whole book) — always include **+1 page before** the first target page and **+1 page after** the last target page (to avoid cutting off the beginning/end of a section, task, or illustration). If the target page is the first or last in the book, do not add a buffer on that side.
3. **Determine the needed pages** using one of these methods:
   - by page range (e.g., "pages 3–4")
   - by text/phrase (find which pages contain the phrase/heading)
   - by section/heading (find the start/end of the section and collect all pages in that section)
4. **Build a new PDF** from the expanded page range (target + buffer pages):
   - take only the identified pages from the original;
   - combine into a single new document (name format: `<slug>_extract_<topic>.pdf`).
5. **Send the PDF** to the user.
6. **Add a brief explanation**: which book, which pages, why these specific pages (indicate both target and added "buffer" pages).

If the user needs the **entire book** — send the file at `original_path` without extraction.

## Step 5 — Homework context

If the request is related to homework:

1. Check current homework via `list_homeworks(status="pending")`.
2. Extract hints from the homework description: subject, lesson, topic.
3. Use this information to search for the book (step 2).

Example: homework "Complete task 2 from lesson 5" → search for a book by the homework's subject, lesson 5, task 2.

## Tools used

- `list_books` — search books (filter by `subject_id`, `has_summary`)
- `get_book` — get a book by ID (contains `original_path`, `summary_path`, `original_filename`)
- `list_subjects` — list of subjects for determining `subject_id`
- `list_homeworks` — list of homework (for request context)
"""

BOOKS_WORKFLOW_INSTRUCTIONS = """\
# Books workflow — storing and registering books in Learning Hub

Goal: uniformly accept books (from the `temp_book/` folder on the server), store them in the file structure, generate a brief `book.md`, and register them in Learning Hub.

## 1) Storage base

All books are stored in:

`/home/eva/.openclaw/workspace/school`

A separate folder is created for each book:

`/home/eva/.openclaw/workspace/school/<book_slug>/`

Folder contents:
- `original.pdf` — the original book file
- `book.md` — brief description + approximate table of contents

---

## 2) `book.md` format

Recommended template:

```md
# <Book title>

## Summary
<2–6 sentences: what the book is about, what level, what it covers>

## Subject
- Subject (Learning Hub): <name>
- Subject ID: <id>

## Approximate table of contents
1. ...
2. ...
3. ...

## Key topics
- ...
- ...
- ...

## Source
- Original file: ./original.pdf
- Added at: <YYYY-MM-DD HH:mm Europe/Vienna>
```

---

## 3) Linking to a subject (Learning Hub)

### 3.1 Determining the subject
For each book, determine the subject:
- by file name,
- by cover/first pages,
- by keywords/table of contents.

### 3.2 Checking against the subject database
- Check existing subjects via `list_subjects`.
- If the subject is found — use its `subject_id`.

### 3.3 If the subject is undetermined or missing
If the subject cannot be determined or it doesn't exist in Learning Hub:
1. suggest a subject option to the user;
2. wait for confirmation;
3. only after confirmation proceed with processing the book.

---

## 4) Registering the book in Learning Hub

After preparing the folder and `book.md`, call:

- `add_book`

Fields:
- `title` (required):
  - first try to extract from the book itself;
  - if unsuccessful — take from the file name.
- `original_filename` (required): priority for determining:
  1. **Name from the document card in Telegram** (what the user sees in the interface) — use first. **Record strictly as-is, without corrections, without "improvements", without renaming** — even if the name looks messy, has typos, or is in transliteration.
  2. Only if there is no document card at all — use the technical file name (e.g., `file_123.pdf`).
- `description` (optional): brief description from `book.md`
- `original_path`: absolute path to `original.pdf`
- `summary_path`: absolute path to `book.md`
- `subject_id` (optional but recommended): id of the selected/confirmed subject

---

## 5) Adding books — receiving files

**Important: do not accept files via messengers (Telegram, etc.).** When forwarding through a messenger, file names get corrupted, leading to loss of the original name and errors during registration.

If a user writes that they want to add books:

1. **Refuse to accept files via messenger.** Explain that file names arrive incorrectly through messengers.
2. **Ask to place the files on the server** in the folder:
   `/home/eva/.openclaw/workspace/workflows/temp_book/`
3. When the user confirms the files are in place — **process the contents of `temp_book/`**:
   - scan the folder, collect the list of files;
   - for each file `original_filename` = file name from the folder (as-is, without changes);
   - determine the assumed subject;
   - check the subject against Learning Hub:
     - if found — record the `subject_id`;
     - if not found/unclear — ask the user for confirmation;
   - after confirmation, process each book:
     - create folder `school/<book_slug>/`;
     - copy the file as `original.pdf`;
     - prepare `book.md` (brief description + approximate table of contents);
     - register the book via `add_book`.
4. Send a summary report to the user:
   - what was added,
   - which `subject_id` values were used,
   - which books require further clarification (if any).
5. After successful processing — **delete the processed files from `temp_book/`**.

---

## 6) Quality requirements

- `book.md` should be short enough for quick reading, but contain a guide to the book's structure.
- An **approximate** table of contents is acceptable if the full ToC is unavailable.
- Do not guess the subject — if uncertain, ask for confirmation.
- Save all paths in absolute form for stable tool operation.

## Tools used

- `add_book` — register a new book
- `list_books` — check existing books
- `list_subjects` — check existing subjects
- `get_book` — get book details
"""


def register_instruction_tools(mcp: FastMCP) -> None:
    """Register instruction tools that return workflow guides for the agent."""

    @mcp.tool(description="""\
      Get step-by-step instructions for finding and delivering educational materials (textbooks).

      Call this tool when a user asks for a textbook, specific pages, lesson materials,
      or anything related to looking up educational content from the book library.

      Returns a detailed algorithm the agent should follow to search, identify,
      extract, and deliver the right book or pages to the user.""")
    async def get_book_lookup_instructions() -> str:
        return BOOK_LOOKUP_INSTRUCTIONS

    @mcp.tool(description="""\
      Get step-by-step instructions for processing and registering new books into Learning Hub.

      Call this tool when new book files need to be added to the system — typically from
      the temp_book/ folder on the server. Covers the full workflow: creating storage folders,
      generating book.md summaries, linking to subjects, and registering via add_book.

      Returns a detailed algorithm the agent should follow to process and register books.""")
    async def get_books_workflow_instructions() -> str:
        return BOOKS_WORKFLOW_INSTRUCTIONS
