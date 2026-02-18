"""System readiness check tool for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.school import SchoolRepository
from learning_hub.tools.tool_names import (
    TOOL_CHECK_SYSTEM_READINESS,
    TOOL_LIST_SCHOOLS,
    TOOL_SET_CONFIG,
    TOOL_UPDATE_SCHOOL,
)


class ReadinessIssue(BaseModel):
    """A single readiness issue that needs to be resolved."""
    check: str
    message: str
    fix_hint: str


class ReadinessResponse(BaseModel):
    """System readiness check result."""
    ready: bool
    issues: list[ReadinessIssue]


def register_readiness_tools(mcp: FastMCP) -> None:
    """Register system readiness tools."""

    @mcp.tool(name=TOOL_CHECK_SYSTEM_READINESS, description="""Check if the system is ready for use.

    Runs a series of checks to verify the system is properly configured.
    Call this at the start of a session to identify missing setup steps.

    Checks performed:
    - At least one school must be active
    - All required config entries must have values set

    Returns:
        ReadinessResponse with ready=true if all checks pass,
        or ready=false with a list of issues to resolve
    """)
    async def check_system_readiness() -> ReadinessResponse:
        issues: list[ReadinessIssue] = []

        async with AsyncSessionLocal() as session:
            # Check 1: At least one active school
            school_repo = SchoolRepository(session)
            active_schools = await school_repo.list(is_active=True)
            if not active_schools:
                issues.append(ReadinessIssue(
                    check="active_school",
                    message="No active schools in the system. "
                            "At least one school must be activated.",
                    fix_hint=f"Call {TOOL_LIST_SCHOOLS}() to see available schools, "
                             f"then {TOOL_UPDATE_SCHOOL}(school_id=..., is_active=true) "
                             f"to activate the ones you need.",
                ))

            # Check 2: Required configs must be set
            config_repo = ConfigEntryRepository(session)
            unset_configs = await config_repo.list_required_unset()
            for entry in unset_configs:
                issues.append(ReadinessIssue(
                    check="required_config",
                    message=f"Required config '{entry.key}' is not set. "
                            f"Description: {entry.description}",
                    fix_hint=f"Call {TOOL_SET_CONFIG}(key='{entry.key}', value='...')",
                ))

        return ReadinessResponse(
            ready=len(issues) == 0,
            issues=issues,
        )
