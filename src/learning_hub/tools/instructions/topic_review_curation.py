from learning_hub.tools.tool_names import (
    TOOL_LIST_SUBJECTS,
    TOOL_LIST_TOPIC_REVIEWS,
    TOOL_MARK_TOPIC_REINFORCED,
    TOOL_RUN_SYNC,
)

TOPIC_REVIEW_CURATION_INSTRUCTIONS = f"""\
# TopicReview curation after sync

> Call this tool after `{TOOL_RUN_SYNC}`.
> The sync may create TopicReview records for subjects that don't require
> academic reinforcement (PE, crafts, music, art, etc.).
> This instruction describes how to clean them up.

## Principle

Close TopicReviews for **non-academic subjects** — those where
reinforcement/review through bonus tasks doesn't make sense.

Examples of such subjects (any language):
- PE / physical education
- Crafts / workshop
- Music
- Art / drawing

This is not an exhaustive list. If you encounter another clearly non-academic \
subject — close it using the same principle. \
Judge by the subject name regardless of language.

---

## Algorithm

### Step 1 — Get subjects map

Call `{TOOL_LIST_SUBJECTS}()` and build a mapping: `subject_id → subject_name`.

### Step 2 — Get pending reviews

Call `{TOOL_LIST_TOPIC_REVIEWS}(status="pending")`.

If the list is empty — nothing to curate. **Stop.**

### Step 3 — Identify irrelevant reviews

For each pending TopicReview:
1. Look up `subject_name` by `subject_id` from the mapping.
2. Determine whether the subject is non-academic (see principle above).
3. If yes — mark for closure.

### Step 4 — Close irrelevant reviews

For each irrelevant review, call:
`{TOOL_MARK_TOPIC_REINFORCED}(review_id=<id>)`

### Step 5 — Report

Report how many reviews were closed and which subjects they belonged to.

---

## Tools used

- `{TOOL_LIST_SUBJECTS}` — subject id→name mapping
- `{TOOL_LIST_TOPIC_REVIEWS}` — get pending reviews
- `{TOOL_MARK_TOPIC_REINFORCED}` — close irrelevant review
"""
