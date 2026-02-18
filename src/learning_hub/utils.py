"""Shared utility functions."""

from datetime import datetime


def dt_to_str(dt: datetime | None) -> str | None:
    """Convert datetime to ISO format string.

    SQLite stores datetimes with a space separator (2026-02-03 13:58:44),
    but JSON Schema date-time format requires 'T' (2026-02-03T13:58:44).
    Using .isoformat() ensures the correct format.
    """
    return dt.isoformat() if dt else None
