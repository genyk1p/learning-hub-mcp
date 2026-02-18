"""Repository for School model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.school import School


class SchoolRepository:
    """Repository for School CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        code: str,
        name: str,
        grading_system: str | None = None,
        is_active: bool = False,
    ) -> School:
        """Create a new school."""
        school = School(
            code=code.upper(),
            name=name,
            grading_system=grading_system,
            is_active=is_active,
        )
        self.session.add(school)
        await self.session.commit()
        await self.session.refresh(school)
        return school

    async def get_by_id(self, school_id: int) -> School | None:
        """Get school by ID."""
        return await self.session.get(School, school_id)

    async def get_by_code(self, code: str) -> School | None:
        """Get school by country code."""
        query = select(School).where(School.code == code.upper())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, is_active: bool | None = None) -> list[School]:
        """List schools with optional active filter."""
        query = select(School).order_by(School.code)

        if is_active is not None:
            query = query.where(School.is_active == is_active)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        school_id: int,
        name: str | None = None,
        grading_system: str | None = None,
        is_active: bool | None = None,
        clear_grading_system: bool = False,
    ) -> School | None:
        """Update school fields. Returns None if not found."""
        school = await self.get_by_id(school_id)
        if school is None:
            return None

        if name is not None:
            school.name = name
        if clear_grading_system:
            school.grading_system = None
        elif grading_system is not None:
            school.grading_system = grading_system
        if is_active is not None:
            school.is_active = is_active

        await self.session.commit()
        await self.session.refresh(school)
        return school
