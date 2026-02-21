"""Repository for FamilyMember model."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.family_member import FamilyMember
from learning_hub.models.enums import FamilyRole


class FamilyMemberRepository:
    """Repository for FamilyMember CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        role: FamilyRole,
        full_name: str | None = None,
        is_admin: bool = False,
        is_student: bool = False,
        notes: str | None = None,
        birth_date: date | None = None,
    ) -> FamilyMember:
        """Create a new family member."""
        if birth_date is not None and birth_date > date.today():
            raise ValueError(
                f"birth_date {birth_date.isoformat()} is in the future."
            )
        if is_student and birth_date is None:
            raise ValueError("birth_date is required for student.")

        member = FamilyMember(
            name=name,
            role=role,
            full_name=full_name,
            is_admin=is_admin,
            is_student=is_student,
            notes=notes,
            birth_date=birth_date,
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        """Get family member by ID."""
        return await self.session.get(FamilyMember, member_id)

    async def get_student(self) -> FamilyMember | None:
        """Get the single student record."""
        query = select(FamilyMember).where(FamilyMember.is_student.is_(True))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        role: FamilyRole | None = None,
    ) -> list[FamilyMember]:
        """List family members with optional filters."""
        query = select(FamilyMember)

        if role is not None:
            query = query.where(FamilyMember.role == role)

        query = query.order_by(FamilyMember.id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        member_id: int,
        name: str | None = None,
        full_name: str | None = None,
        role: FamilyRole | None = None,
        is_admin: bool | None = None,
        notes: str | None = None,
        clear_notes: bool = False,
        birth_date: date | None = None,
        clear_birth_date: bool = False,
    ) -> FamilyMember | None:
        """Update family member fields. Returns None if not found."""
        member = await self.get_by_id(member_id)
        if member is None:
            return None

        if name is not None:
            member.name = name
        if full_name is not None:
            member.full_name = full_name
        if role is not None:
            member.role = role
        if is_admin is not None:
            member.is_admin = is_admin
        if clear_notes:
            member.notes = None
        elif notes is not None:
            member.notes = notes
        if birth_date is not None and birth_date > date.today():
            raise ValueError(
                f"birth_date {birth_date.isoformat()} is in the future."
            )

        # Validate before mutating to avoid dirty ORM state
        effective_birth_date = member.birth_date
        if clear_birth_date:
            effective_birth_date = None
        elif birth_date is not None:
            effective_birth_date = birth_date

        if member.is_student and effective_birth_date is None:
            raise ValueError("birth_date is required for student.")

        # Safe to mutate now
        if clear_birth_date:
            member.birth_date = None
        elif birth_date is not None:
            member.birth_date = birth_date

        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def delete(self, member_id: int) -> bool:
        """Delete a family member. Returns True if deleted, False if not found."""
        member = await self.get_by_id(member_id)
        if member is None:
            return False

        await self.session.delete(member)
        await self.session.commit()
        return True
