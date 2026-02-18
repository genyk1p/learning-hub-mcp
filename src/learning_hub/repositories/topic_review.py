"""Repository for TopicReview model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from learning_hub.models.grade import Grade
from learning_hub.models.topic_review import TopicReview
from learning_hub.models.enums import TopicReviewStatus


class TopicReviewRepository:
    """Repository for TopicReview CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_id: int,
        subject_topic_id: int,
        grade_id: int,
    ) -> TopicReview:
        """Create a new topic review."""
        review = TopicReview(
            subject_id=subject_id,
            subject_topic_id=subject_topic_id,
            grade_id=grade_id,
            status=TopicReviewStatus.PENDING,
            repeat_count=0,
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def get_by_id(self, review_id: int) -> TopicReview | None:
        """Get topic review by ID with related grade, subject and topic."""
        query = (
            select(TopicReview)
            .where(TopicReview.id == review_id)
            .options(
                selectinload(TopicReview.grade),
                selectinload(TopicReview.subject),
                selectinload(TopicReview.subject_topic),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_grade_id(self, grade_id: int) -> TopicReview | None:
        """Get topic review by grade ID."""
        query = select(TopicReview).where(TopicReview.grade_id == grade_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        subject_id: int | None = None,
        subject_topic_id: int | None = None,
        status: TopicReviewStatus | None = None,
    ) -> list[TopicReview]:
        """List topic reviews with optional filters."""
        query = select(TopicReview)

        if subject_id is not None:
            query = query.where(TopicReview.subject_id == subject_id)

        if subject_topic_id is not None:
            query = query.where(TopicReview.subject_topic_id == subject_topic_id)

        if status is not None:
            query = query.where(TopicReview.status == status)

        query = query.order_by(TopicReview.created_at.desc())

        query = query.options(
            selectinload(TopicReview.grade),
            selectinload(TopicReview.subject),
            selectinload(TopicReview.subject_topic),
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_top_priority_candidates(
        self, limit: int = 4,
    ) -> list[TopicReview]:
        """Get top-priority pending TopicReviews.

        Priority: worse grade > fewer repeats > more recent.
        Returns up to `limit` candidates for random selection.
        """
        query = (
            select(TopicReview)
            .join(TopicReview.grade)
            .where(TopicReview.status == TopicReviewStatus.PENDING)
            .order_by(
                Grade.grade_value.desc(),
                TopicReview.repeat_count.asc(),
                TopicReview.created_at.desc(),
            )
            .limit(limit)
            .options(
                selectinload(TopicReview.grade),
                selectinload(TopicReview.subject),
                selectinload(TopicReview.subject_topic),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_reinforced(self, review_id: int) -> TopicReview | None:
        """Mark topic review as reinforced. Returns None if not found."""
        review = await self.get_by_id(review_id)
        if review is None:
            return None

        review.status = TopicReviewStatus.REINFORCED
        await self.session.commit()
        # Re-fetch with eager loading (refresh doesn't reload relationships)
        return await self.get_by_id(review_id)

    async def increment_repeat_count(self, review_id: int) -> TopicReview | None:
        """Increment repeat count by 1. Returns None if not found."""
        review = await self.get_by_id(review_id)
        if review is None:
            return None

        review.repeat_count += 1
        await self.session.commit()
        # Re-fetch with eager loading (refresh doesn't reload relationships)
        return await self.get_by_id(review_id)
