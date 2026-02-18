"""Repository for Subject model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.subject import Subject


class SubjectRepository:
    """Repository for Subject CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        school_id: int,
        name: str,
        name_ru: str | None = None,
        grade_level: int | None = None,
        is_active: bool = True,
    ) -> Subject:
        """Create a new subject."""
        subject = Subject(
            school_id=school_id,
            name=name,
            name_ru=name_ru,
            grade_level=grade_level,
            is_active=is_active,
        )
        self.session.add(subject)
        await self.session.commit()
        await self.session.refresh(subject)
        return subject

    async def get_by_id(self, subject_id: int) -> Subject | None:
        """Get subject by ID."""
        return await self.session.get(Subject, subject_id)

    async def get_by_name(self, school_id: int, name: str) -> Subject | None:
        """Get subject by school_id and name."""
        query = select(Subject).where(
            Subject.school_id == school_id,
            Subject.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create(self, school_id: int, name: str) -> tuple[Subject, bool]:
        """Get subject by name or create if not exists.

        Returns:
            Tuple of (subject, created) where created is True if new subject was created.
        """
        subject = await self.get_by_name(school_id, name)
        if subject is not None:
            return subject, False

        subject = await self.create(school_id=school_id, name=name)
        return subject, True

    async def list(
        self,
        school_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Subject]:
        """List subjects with optional filters."""
        query = select(Subject)

        if school_id is not None:
            query = query.where(Subject.school_id == school_id)

        if is_active is not None:
            query = query.where(Subject.is_active == is_active)

        query = query.order_by(Subject.school_id, Subject.name)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        subject_id: int,
        name: str | None = None,
        name_ru: str | None = None,
        grade_level: int | None = None,
        is_active: bool | None = None,
        current_book_id: int | None = None,
        clear_current_book: bool = False,
        tutor_id: int | None = None,
        clear_tutor: bool = False,
    ) -> Subject | None:
        """Update subject fields. Returns None if not found."""
        subject = await self.get_by_id(subject_id)
        if subject is None:
            return None

        if name is not None:
            subject.name = name
        if name_ru is not None:
            subject.name_ru = name_ru
        if grade_level is not None:
            subject.grade_level = grade_level
        if is_active is not None:
            subject.is_active = is_active
        if clear_current_book:
            subject.current_book_id = None
        elif current_book_id is not None:
            subject.current_book_id = current_book_id
        if clear_tutor:
            subject.tutor_id = None
        elif tutor_id is not None:
            subject.tutor_id = tutor_id

        await self.session.commit()
        await self.session.refresh(subject)
        return subject
