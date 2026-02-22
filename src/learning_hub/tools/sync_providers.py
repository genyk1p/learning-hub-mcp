"""Sync provider tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import SyncProviderType
from learning_hub.repositories.sync_provider import SyncProviderRepository
from learning_hub.sync import SYNC_HANDLERS
from learning_hub.sync.result import ProviderSyncResult, RunSyncResult
from learning_hub.tools.tool_names import (
    TOOL_GET_GRADE_ESCALATION_INSTRUCTIONS,
    TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS,
    TOOL_LIST_SYNC_PROVIDERS,
    TOOL_RUN_SYNC,
    TOOL_UPDATE_SYNC_PROVIDER,
)
from learning_hub.utils import dt_to_str


class SyncProviderResponse(BaseModel):
    """Sync provider response schema."""
    id: int
    code: str
    name: str
    is_active: bool
    school_id: int | None
    school_code: str | None
    school_name: str | None
    updated_at: str | None
    recommendation: str | None = None


def _to_response(p) -> SyncProviderResponse:
    """Convert SyncProvider ORM object to response."""
    return SyncProviderResponse(
        id=p.id,
        code=p.code,
        name=p.name,
        is_active=p.is_active,
        school_id=p.school_id,
        school_code=p.school.code if p.school else None,
        school_name=p.school.name if p.school else None,
        updated_at=dt_to_str(p.updated_at),
    )


def register_sync_provider_tools(mcp: FastMCP) -> None:
    """Register sync provider management tools."""

    @mcp.tool(name=TOOL_LIST_SYNC_PROVIDERS, description="""List all sync providers.

    Shows all available sync services (e.g. EduPage) with their
    activation status and linked school.

    Returns:
        List of all sync providers ordered by code
    """)
    async def list_sync_providers() -> list[SyncProviderResponse]:
        async with AsyncSessionLocal() as session:
            repo = SyncProviderRepository(session)
            providers = await repo.list_all()
            return [_to_response(p) for p in providers]

    @mcp.tool(name=TOOL_UPDATE_SYNC_PROVIDER, description="""Update a sync provider.

    Link a provider to a school and/or activate/deactivate it.
    No validation on school status — sync tools check at runtime.

    Args:
        provider_id: ID of the sync provider to update
        is_active: Set active status (optional)
        school_id: Link to a school by ID (optional)
        clear_school: Set to true to unlink the school (optional)

    Returns:
        Updated sync provider or null if not found
    """)
    async def update_sync_provider(
        provider_id: int,
        is_active: bool | None = None,
        school_id: int | None = None,
        clear_school: bool = False,
    ) -> SyncProviderResponse | str:
        async with AsyncSessionLocal() as session:
            repo = SyncProviderRepository(session)
            try:
                provider = await repo.update(
                    provider_id=provider_id,
                    is_active=is_active,
                    school_id=school_id,
                    clear_school=clear_school,
                )
            except ValueError as e:
                return str(e)
            except IntegrityError:
                return (
                    f"Cannot link school_id={school_id} — "
                    "it is already linked to another sync provider. "
                    "Each school can only have one sync provider."
                )
            if provider is None:
                return f"Sync provider with id={provider_id} not found"

            response = _to_response(provider)

            # When provider was just activated, nudge the agent
            if is_active is True and provider.is_active:
                response.recommendation = (
                    f"Dear Agent, if you're reading this letter — congratulations, "
                    f"the sync provider '{provider.name}' is now active and linked "
                    f"to school '{provider.school.name if provider.school else '?'}'! "
                    f"But don't celebrate just yet.\n\n"
                    f"Here's the thing: in most cases a sync provider runs as a "
                    f"background cron job — which means if something goes wrong, "
                    f"you won't be around to tell the user about it. That's why "
                    f"your next steps are important:\n\n"
                    f"1. SUGGEST A TEST RUN: Ask the user to run a one-time sync "
                    f"right now to verify credentials and data flow. It's much "
                    f"better to catch problems now than to discover issues later "
                    f"when nobody is watching.\n\n"
                    f"2. SET UP A CRON JOB: If you're working within the OpenClaw "
                    f"ecosystem, the only reliable way to keep data in sync is a "
                    f"cron job that runs at least once daily. Check if such a cron "
                    f"already exists in your system — if not, inform the user and "
                    f"suggest creating one.\n\n"
                    f"IMPORTANT about cron timing: the sync triggers grade "
                    f"escalation which may send notifications to tutors and "
                    f"admins. Schedule the cron for reasonable daytime hours "
                    f"(e.g. 15:00–18:00, after school) — NOT at 3 AM when "
                    f"everyone is asleep. Nobody wants a 'your kid got a 5' "
                    f"message at dawn.\n\n"
                    f"Good luck out there, and may all your syncs be successful!"
                )

            return response

    @mcp.tool(name=TOOL_RUN_SYNC, description="""Run sync for active providers.

    Finds all active sync providers (or a specific one by code) and
    executes the sync handler for each — fetching grades, homeworks, etc.
    from external services into the local database.

    Args:
        provider_code: Optional provider code to sync only one provider
            (e.g. "edupage"). If omitted, syncs ALL active providers.

    Returns:
        Combined sync results for all processed providers with
        a recommendation for post-sync actions if grades were synced.
    """)
    async def run_sync(
        provider_code: str | None = None,
    ) -> RunSyncResult:
        async with AsyncSessionLocal() as session:
            repo = SyncProviderRepository(session)

            if provider_code is not None:
                # Sync a specific provider
                provider = await repo.get_by_code(provider_code)
                if provider is None:
                    return RunSyncResult(
                        providers_processed=0,
                        results=[],
                        recommendation=(
                            f"Provider with code='{provider_code}' not found. "
                            f"Use {TOOL_LIST_SYNC_PROVIDERS} to see available providers."
                        ),
                    )
                if not provider.is_active:
                    return RunSyncResult(
                        providers_processed=0,
                        results=[],
                        recommendation=(
                            f"Provider '{provider.name}' is not active. "
                            f"Use {TOOL_UPDATE_SYNC_PROVIDER} to activate it first."
                        ),
                    )
                providers = [provider]
            else:
                # Sync all active providers
                providers = await repo.list_active()
                if not providers:
                    return RunSyncResult(
                        providers_processed=0,
                        results=[],
                        recommendation=(
                            "No active sync providers found. "
                            f"Use {TOOL_LIST_SYNC_PROVIDERS} to check, "
                            f"{TOOL_UPDATE_SYNC_PROVIDER} to activate."
                        ),
                    )

            results: list[ProviderSyncResult] = []

            for provider in providers:
                # Look up handler by provider code
                try:
                    provider_type = SyncProviderType(provider.code)
                except ValueError:
                    results.append(ProviderSyncResult(
                        provider_code=provider.code,
                        provider_name=provider.name,
                        school_name=(
                            provider.school.name if provider.school else None
                        ),
                        errors=[
                            f"Unknown provider type '{provider.code}' — "
                            "no sync handler registered."
                        ],
                    ))
                    continue

                handler = SYNC_HANDLERS.get(provider_type)
                if handler is None:
                    results.append(ProviderSyncResult(
                        provider_code=provider.code,
                        provider_name=provider.name,
                        school_name=(
                            provider.school.name if provider.school else None
                        ),
                        errors=[
                            f"No sync handler for '{provider.code}'. "
                            "Handler not implemented yet."
                        ],
                    ))
                    continue

                try:
                    result = await handler(session, provider)
                except Exception as e:
                    result = ProviderSyncResult(
                        provider_code=provider.code,
                        provider_name=provider.name,
                        school_name=(
                            provider.school.name
                            if provider.school else None
                        ),
                        errors=[
                            f"Sync handler crashed for "
                            f"'{provider.code}': "
                            f"{type(e).__name__}: {e}"
                        ],
                    )
                results.append(result)

            # Build recommendation if grades were synced
            total_grades = sum(r.grades_created for r in results)
            total_errors = sum(len(r.errors) for r in results)
            recommendation = None
            if total_grades > 0:
                recommendation = (
                    f"Dear Agent, if you're reading this letter — the sync "
                    f"has completed and {total_grades} new grade(s) landed in "
                    f"the database. But your job isn't done yet!\n\n"
                    f"Among those grades there may be bad ones (3, 4, or 5) "
                    f"that responsible adults need to know about. Your next "
                    f"steps are MANDATORY:\n\n"
                    f"1. Call `{TOOL_GET_GRADE_ESCALATION_INSTRUCTIONS}()` "
                    f"and follow the returned algorithm to escalate bad "
                    f"grades to tutors or admins.\n\n"
                    f"2. Call `{TOOL_GET_TOPIC_REVIEW_CURATION_INSTRUCTIONS}()` "
                    f"and follow the returned algorithm to clean up "
                    f"TopicReviews for non-academic subjects (PE, music, "
                    f"art, etc.) that don't need reinforcement.\n\n"
                    f"Don't skip these steps — the whole point of syncing "
                    f"is to act on the data, not just collect it!"
                )
            elif total_errors > 0:
                recommendation = (
                    "Sync completed but with errors. Check the errors "
                    "in each provider result for details."
                )

            return RunSyncResult(
                providers_processed=len(providers),
                results=results,
                recommendation=recommendation,
            )
