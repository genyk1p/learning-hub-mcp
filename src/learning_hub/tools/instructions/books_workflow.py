from learning_hub.tools.config_vars import CFG_BOOKS_STORAGE_DIR, CFG_TEMP_BOOK_DIR
from learning_hub.tools.tool_names import (
    TOOL_ADD_BOOK,
    TOOL_GET_BOOK,
    TOOL_GET_CONFIG,
    TOOL_LIST_BOOKS,
    TOOL_LIST_SCHOOLS,
    TOOL_LIST_SUBJECTS,
    TOOL_UPDATE_BOOK,
)

BOOKS_WORKFLOW_INSTRUCTIONS = f"""\
# Books workflow — storing and registering books in Learning Hub

Goal: uniformly accept books, store them in the file structure, generate a brief `book.md`, and register them in Learning Hub.

## 0) Resolve paths from config

Before processing, retrieve paths from Learning Hub config:
- Call `{TOOL_GET_CONFIG}(key="{CFG_TEMP_BOOK_DIR}")` — staging folder where users place book files.
- Call `{TOOL_GET_CONFIG}(key="{CFG_BOOKS_STORAGE_DIR}")` — base folder for processed books.

If either config is not set (value is null) — inform the user and **stop**.

## 1) Storage base

All books are stored in the `{CFG_BOOKS_STORAGE_DIR}` path (from config).

A separate folder is created for each book:

`{CFG_BOOKS_STORAGE_DIR}/<book_slug>/`

Folder contents:
- `original.pdf` — the original book file
- `book.md` — brief description + approximate table of contents
- `contents.md` — index of markdown chunks (which file covers which topics/pages)
- `parts/` — folder with markdown chunks of the book (part_01.md, part_02.md, ...)

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
- Call `{TOOL_LIST_SCHOOLS}(is_active=true)` — get active schools to narrow down subjects.
- Check existing subjects via `{TOOL_LIST_SUBJECTS}(school_id=<id>)` \
(filter by school if only one is active, or if the school is clear from the book content).
- If the subject is found — use its `subject_id`.

### 3.3 If the subject is undetermined or missing
If the subject cannot be determined or it doesn't exist in Learning Hub:
1. suggest a subject option to the user;
2. wait for confirmation;
3. only after confirmation proceed with processing the book.

---

## 4) Converting PDF to markdown chunks

After creating the book folder and `book.md`, convert the entire book to markdown:

### 4.1 Splitting into chunks

1. Read the PDF page by page.
2. Group pages into chunks of **10–15 pages** each (~5–9k tokens per chunk).
3. Convert each chunk to markdown, preserving:
   - headings and structure
   - lists, tables
   - task numbers and exercise text
   - important formatting (bold, italic)
4. Save each chunk as `parts/part_01.md`, `parts/part_02.md`, etc.

### 4.2 Creating the contents index (`contents.md`)

After all chunks are ready, create `contents.md` — a compact index file that maps each chunk to its content.

Recommended format:

```md
# <Book title> — Contents

## part_01.md
Pages 1–12. Chapter 1: Natural numbers. Topics: divisibility, GCD, LCM.

## part_02.md
Pages 13–25. Chapter 2: Fractions. Topics: addition, subtraction of common fractions.

## part_03.md
Pages 26–38. Chapter 3: Decimal fractions. Topics: multiplication, division.
```

Each entry should include:
- **file name** (part_XX.md)
- **page range** from the original PDF
- **chapter / section name** (if identifiable)
- **key topics** covered (2–5 keywords)

Keep entries short — the whole file should be quickly scannable by the agent.

---

## 5) Registering the book in Learning Hub

After preparing the folder, `book.md`, and markdown chunks with `contents.md`, call:

- `{TOOL_ADD_BOOK}`

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
- `contents_path`: absolute path to `contents.md` (optional, set after markdown conversion)
- `subject_id` (optional but recommended): id of the selected/confirmed subject

---

## 6) Adding books — receiving files

**Important: do not accept files via messengers (Telegram, etc.).** When forwarding through a messenger, file names get corrupted, leading to loss of the original name and errors during registration.

If a user writes that they want to add books:

1. **Refuse to accept files via messenger.** Explain that file names arrive incorrectly through messengers.
2. **Ask to place the files on the server** in the folder:
   `{CFG_TEMP_BOOK_DIR}`
3. When the user confirms the files are in place — **process the contents of `{CFG_TEMP_BOOK_DIR}`**:
   - scan the folder, collect the list of files;
   - for each file `original_filename` = file name from the folder (as-is, without changes);
   - determine the assumed subject;
   - check the subject against Learning Hub:
     - if found — record the `subject_id`;
     - if not found/unclear — ask the user for confirmation;
   - after confirmation, process each book:
     - create folder `{CFG_BOOKS_STORAGE_DIR}/<book_slug>/`;
     - copy the file as `original.pdf`;
     - prepare `book.md` (brief description + approximate table of contents);
     - convert PDF to markdown chunks (see section 4);
     - create `contents.md` index;
     - register the book via `{TOOL_ADD_BOOK}`.
4. Send a summary report to the user:
   - what was added,
   - which `subject_id` values were used,
   - which books require further clarification (if any).
5. After successful processing — **delete the processed files from `{CFG_TEMP_BOOK_DIR}`**.

---

## 7) Quality requirements

- `book.md` should be short enough for quick reading, but contain a guide to the book's structure.
- An **approximate** table of contents is acceptable if the full ToC is unavailable.
- Do not guess the subject — if uncertain, ask for confirmation.
- Save all paths in absolute form for stable tool operation.
- Markdown chunks should be self-contained and readable — do not split in the middle of a section or exercise.
- `contents.md` should be compact — the agent must be able to read it in one go to find the right chunk.

## Tools used

- `{TOOL_GET_CONFIG}` — read config values (paths)
- `{TOOL_ADD_BOOK}` — register a new book
- `{TOOL_LIST_BOOKS}` — check existing books
- `{TOOL_LIST_SCHOOLS}` — get active schools to narrow down subjects
- `{TOOL_LIST_SUBJECTS}` — check existing subjects
- `{TOOL_GET_BOOK}` — get book details
- `{TOOL_UPDATE_BOOK}` — update book fields (e.g. set `contents_path` after markdown conversion)
"""
