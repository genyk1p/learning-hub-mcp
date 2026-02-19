"""System readiness check tool for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.family_member import FamilyMemberRepository
from learning_hub.repositories.school import SchoolRepository
from learning_hub.tools.tool_names import (
    TOOL_CHECK_SYSTEM_READINESS,
    TOOL_CREATE_FAMILY_MEMBER,
    TOOL_LIST_FAMILY_MEMBERS,
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
    - At least one family member with is_admin=true must exist
    - Exactly one family member with is_student=true must exist
    - At least one school must be active
    - All required config entries must have values set

    Returns:
        ReadinessResponse with ready=true if all checks pass,
        or ready=false with a list of issues to resolve
    """)
    async def check_system_readiness() -> ReadinessResponse:
        issues: list[ReadinessIssue] = []

        async with AsyncSessionLocal() as session:
            # Check 1: At least one admin
            family_repo = FamilyMemberRepository(session)
            all_members = await family_repo.list()
            admins = [m for m in all_members if m.is_admin]
            students = [m for m in all_members if m.is_student]

            if not admins:
                issues.append(ReadinessIssue(
                    check="admin_member",
                    message="No family member with is_admin=true. "
                            "At least one admin is required for the system to work.",
                    fix_hint=f"Call {TOOL_CREATE_FAMILY_MEMBER}(name=..., role=..., "
                             f"is_admin=true) to create an admin.",
                ))

            # Check 2: Exactly one student
            if len(students) == 0:
                issues.append(ReadinessIssue(
                    check="student_member",
                    message="No family member with is_student=true. "
                            "Exactly one student is required for the system to work.",
                    fix_hint=f"Call {TOOL_CREATE_FAMILY_MEMBER}(name=..., role='student', "
                             f"is_student=true) to create the student.",
                ))
            elif len(students) > 1:
                names = ", ".join(f"{m.name} (id={m.id})" for m in students)
                issues.append(ReadinessIssue(
                    check="student_member",
                    message=f"Multiple students found: {names}. "
                            f"Exactly one student is allowed.",
                    fix_hint=f"Call {TOOL_LIST_FAMILY_MEMBERS}() to review, "
                             f"then fix by updating extra students with is_student=false.",
                ))

            # Check 3: At least one active school
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

            # Check 4: Required configs must be set
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
