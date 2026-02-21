"""FamilyMember tools for MCP server."""

from datetime import date

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import FamilyRole
from learning_hub.repositories.family_member import FamilyMemberRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_FAMILY_MEMBER,
    TOOL_LIST_FAMILY_MEMBERS,
    TOOL_UPDATE_FAMILY_MEMBER,
    TOOL_DELETE_FAMILY_MEMBER,
    TOOL_GET_STUDENT,
)
from learning_hub.utils import dt_to_str


class FamilyMemberResponse(BaseModel):
    """FamilyMember response schema."""
    id: int
    name: str
    full_name: str | None
    role: str
    is_admin: bool
    is_student: bool
    notes: str | None
    birth_date: str | None
    age: int | None
    created_at: str | None
    updated_at: str | None


def _calc_age(birth_date: date | None) -> int | None:
    """Calculate age in years from birth_date. Returns None if birth_date is None."""
    if birth_date is None:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _to_response(m) -> FamilyMemberResponse:
    return FamilyMemberResponse(
        id=m.id,
        name=m.name,
        full_name=m.full_name,
        role=m.role.value,
        is_admin=m.is_admin,
        is_student=m.is_student,
        notes=m.notes,
        birth_date=m.birth_date.isoformat() if m.birth_date else None,
        age=_calc_age(m.birth_date),
        created_at=dt_to_str(m.created_at),
        updated_at=dt_to_str(m.updated_at),
    )


def register_family_member_tools(mcp: FastMCP) -> None:
    """Register family member related tools."""

    role_options = ", ".join(f'"{r.value}"' for r in FamilyRole)

    @mcp.tool(name=TOOL_CREATE_FAMILY_MEMBER, description=f"""Create a new family member.

    Args:
        name: Display name (how the agent should address them)
        role: Role - one of: {role_options}
        full_name: Full legal name (optional)
        is_admin: Has sudo/admin access (default false)
        is_student: Is the tracked student (default false). Only one student allowed.
        notes: Free text notes for the agent (optional)
        birth_date: Date of birth "YYYY-MM-DD" (required for student)

    Returns:
        Created family member
    """)
    async def create_family_member(
        name: str,
        role: str,
        full_name: str | None = None,
        is_admin: bool = False,
        is_student: bool = False,
        notes: str | None = None,
        birth_date: str | None = None,
    ) -> FamilyMemberResponse | dict:
        try:
            role_enum = FamilyRole(role)
            birth_date_parsed = (
                date.fromisoformat(birth_date) if birth_date is not None else None
            )

            async with AsyncSessionLocal() as session:
                repo = FamilyMemberRepository(session)
                member = await repo.create(
                    name=name,
                    role=role_enum,
                    full_name=full_name,
                    is_admin=is_admin,
                    is_student=is_student,
                    notes=notes,
                    birth_date=birth_date_parsed,
                )
                return _to_response(member)
        except ValueError as e:
            return {"error": str(e)}

    @mcp.tool(name=TOOL_LIST_FAMILY_MEMBERS, description=f"""List family members.

    Args:
        role: Filter by role - one of: {role_options} (optional)

    Returns:
        List of family members
    """)
    async def list_family_members(
        role: str | None = None,
    ) -> list[FamilyMemberResponse]:
        role_enum = FamilyRole(role) if role else None

        async with AsyncSessionLocal() as session:
            repo = FamilyMemberRepository(session)
            members = await repo.list(role=role_enum)
            return [_to_response(m) for m in members]

    @mcp.tool(name=TOOL_UPDATE_FAMILY_MEMBER, description=f"""Update a family member.

    Args:
        member_id: ID of the family member to update
        name: New display name (optional)
        full_name: New full name (optional)
        role: New role - one of: {role_options} (optional)
        is_admin: Set admin status (optional)
        notes: New notes (optional)
        clear_notes: Set to true to remove notes (optional)
        birth_date: New date of birth "YYYY-MM-DD" (optional)
        clear_birth_date: Set to true to remove birth_date (optional)

    Returns:
        Updated family member or null if not found
    """)
    async def update_family_member(
        member_id: int,
        name: str | None = None,
        full_name: str | None = None,
        role: str | None = None,
        is_admin: bool | None = None,
        notes: str | None = None,
        clear_notes: bool = False,
        birth_date: str | None = None,
        clear_birth_date: bool = False,
    ) -> FamilyMemberResponse | dict | None:
        try:
            role_enum = FamilyRole(role) if role else None
            birth_date_parsed = (
                date.fromisoformat(birth_date) if birth_date is not None else None
            )

            async with AsyncSessionLocal() as session:
                repo = FamilyMemberRepository(session)
                member = await repo.update(
                    member_id=member_id,
                    name=name,
                    full_name=full_name,
                    role=role_enum,
                    is_admin=is_admin,
                    notes=notes,
                    clear_notes=clear_notes,
                    birth_date=birth_date_parsed,
                    clear_birth_date=clear_birth_date,
                )
                if member is None:
                    return None
                return _to_response(member)
        except ValueError as e:
            return {"error": str(e)}

    @mcp.tool(name=TOOL_DELETE_FAMILY_MEMBER, description="""Delete a family member.

    Also deletes all their gateways (cascade).

    Args:
        member_id: ID of the family member to delete

    Returns:
        True if deleted, False if not found
    """)
    async def delete_family_member(member_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            repo = FamilyMemberRepository(session)
            return await repo.delete(member_id)

    @mcp.tool(name=TOOL_GET_STUDENT, description="""Get the student (the tracked child).

    Returns the single family member with is_student=true, or null if not configured yet.

    Returns:
        Student family member or null
    """)
    async def get_student() -> FamilyMemberResponse | None:
        async with AsyncSessionLocal() as session:
            repo = FamilyMemberRepository(session)
            member = await repo.get_student()
            if member is None:
                return None
            return _to_response(member)
