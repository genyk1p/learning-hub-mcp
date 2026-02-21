"""Repository for Homework model."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from learning_hub.models.homework import Homework
from learning_hub.models.bonus import Bonus
from learning_hub.models.enums import HomeworkStatus, GradeValue


class HomeworkRepository:
    """Repository for Homework CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_id: int,
        description: str,
        subject_topic_id: int | None = None,
        assigned_at: datetime | None = None,
        deadline_at: datetime | None = None,
        edupage_id: str | None = None,
        status: HomeworkStatus = HomeworkStatus.PENDING,
        book_id: int | None = None,
    ) -> Homework:
        """Create a new homework."""
        homework = Homework(
            subject_id=subject_id,
            description=description,
            subject_topic_id=subject_topic_id,
            assigned_at=assigned_at,
            deadline_at=deadline_at,
            status=status,
            edupage_id=edupage_id,
            book_id=book_id,
        )
        self.session.add(homework)
        await self.session.commit()
        await self.session.refresh(homework)
        return homework

    async def get_by_id(self, homework_id: int) -> Homework | None:
        """Get homework by ID."""
        return await self.session.get(Homework, homework_id)

    async def get_by_edupage_id(self, edupage_id: str) -> Homework | None:
        """Get homework by EduPage ID."""
        query = select(Homework).where(Homework.edupage_id == edupage_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        subject_id: int | None = None,
        status: HomeworkStatus | None = None,
        limit: int = 20,
    ) -> list[Homework]:
        """List homeworks with optional filters."""
        query = select(Homework)

        if subject_id is not None:
            query = query.where(Homework.subject_id == subject_id)

        if status is not None:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.deadline_at.asc().nullslast())
        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_approaching_deadline(
        self,
        delta: timedelta,
    ) -> list[Homework]:
        """List pending homeworks with deadline within given delta from now."""
        now = datetime.now()
        deadline_threshold = now + delta

        query = select(Homework).where(
            Homework.status == HomeworkStatus.PENDING,
            Homework.deadline_at.is_not(None),
            Homework.deadline_at > now,
            Homework.deadline_at <= deadline_threshold,
        ).order_by(Homework.deadline_at.asc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def close_overdue(
        self,
        ontime_bonus: int = 5,
        overdue_penalty: int = -5,
    ) -> list[Homework]:
        """Find all pending homeworks past deadline and complete them.

        Each overdue homework gets status=OVERDUE and bonus via complete().
        Returns the list of closed homeworks.
        """
        now = datetime.now()

        query = select(Homework).where(
            Homework.status == HomeworkStatus.PENDING,
            Homework.deadline_at.is_not(None),
            Homework.deadline_at < now,
        ).order_by(Homework.deadline_at.asc())

        result = await self.session.execute(query)
        overdue = list(result.scalars().all())

        closed = []
        for hw in overdue:
            completed = await self.complete(
                hw.id,
                ontime_bonus=ontime_bonus,
                overdue_penalty=overdue_penalty,
            )
            if completed is not None:
                closed.append(completed)

        return closed

    async def complete(
        self,
        homework_id: int,
        ontime_bonus: int = 5,
        overdue_penalty: int = -5,
        recommended_grade: GradeValue | None = None,
    ) -> Homework | None:
        """Mark homework as completed with bonus minutes.

        If already DONE or OVERDUE — returns homework as-is (nothing to close).
        If PENDING — sets completed_at, checks deadline, assigns status and bonus.
        Creates new bonus or updates existing one for this homework.
        """
        homework = await self.get_by_id(homework_id)
        if homework is None:
            return None

        if homework.status in (HomeworkStatus.DONE, HomeworkStatus.OVERDUE):
            return homework

        if recommended_grade is not None:
            homework.recommended_grade = recommended_grade

        now = datetime.now()
        homework.completed_at = now

        is_overdue = (
            homework.deadline_at is not None
            and now > homework.deadline_at
        )

        if is_overdue:
            homework.status = HomeworkStatus.OVERDUE
            bonus_minutes = overdue_penalty
        else:
            homework.status = HomeworkStatus.DONE
            bonus_minutes = ontime_bonus

        # Find existing bonus for this homework or create new one
        query = select(Bonus).where(Bonus.homework_id == homework_id)
        result = await self.session.execute(query)
        bonus = result.scalar_one_or_none()

        if bonus is not None:
            bonus.minutes = bonus_minutes
            bonus.rewarded = False
        else:
            bonus = Bonus(
                homework_id=homework_id,
                minutes=bonus_minutes,
            )
            self.session.add(bonus)

        await self.session.commit()
        await self.session.refresh(homework)
        return homework

    async def update(
        self,
        homework_id: int,
        description: str | None = None,
        deadline_at: datetime | None = None,
        recommended_grade: GradeValue | None = None,
        book_id: int | None = None,
        clear_book: bool = False,
    ) -> Homework | None:
        """Update homework fields. Returns None if not found.

        Does not change status — use complete() for that.
        """
        homework = await self.get_by_id(homework_id)
        if homework is None:
            return None

        if description is not None:
            homework.description = description
        if deadline_at is not None:
            homework.deadline_at = deadline_at
        if recommended_grade is not None:
            homework.recommended_grade = recommended_grade
        if clear_book:
            homework.book_id = None
        elif book_id is not None:
            homework.book_id = book_id

        await self.session.commit()
        await self.session.refresh(homework)
        return homework

    async def list_pending_with_deadline(self) -> list[Homework]:
        """List pending homeworks that have a deadline, with subject eager-loaded."""
        query = (
            select(Homework)
            .options(joinedload(Homework.subject))
            .where(
                Homework.status == HomeworkStatus.PENDING,
                Homework.deadline_at.is_not(None),
            )
            .order_by(Homework.deadline_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def mark_reminded(
        self,
        d1_homework_ids: list[int],
        d2_homework_ids: list[int],
    ) -> int:
        """Set reminded_d1_at / reminded_d2_at to now for given homework IDs."""
        now = datetime.now()
        count = 0

        if d1_homework_ids:
            stmt = (
                update(Homework)
                .where(Homework.id.in_(d1_homework_ids))
                .values(reminded_d1_at=now)
            )
            result = await self.session.execute(stmt)
            count += result.rowcount

        if d2_homework_ids:
            stmt = (
                update(Homework)
                .where(Homework.id.in_(d2_homework_ids))
                .values(reminded_d2_at=now)
            )
            result = await self.session.execute(stmt)
            count += result.rowcount

        await self.session.commit()
        return count
