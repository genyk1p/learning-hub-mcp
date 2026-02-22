"""Result models for sync operations."""

from pydantic import BaseModel


class ProviderSyncResult(BaseModel):
    """Result of a single provider sync operation."""
    provider_code: str
    provider_name: str
    school_name: str | None
    grades_fetched: int = 0
    grades_created: int = 0
    grades_skipped: int = 0
    homeworks_fetched: int = 0
    homeworks_created: int = 0
    homeworks_skipped: int = 0
    subjects_created: int = 0
    topics_created: int = 0
    reviews_created: int = 0
    errors: list[str] = []


class RunSyncResult(BaseModel):
    """Result of run_sync tool (all providers combined)."""
    providers_processed: int
    results: list[ProviderSyncResult]
    recommendation: str | None = None
