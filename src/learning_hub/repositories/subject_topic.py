"""Repository for SubjectTopic model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.subject_topic import SubjectTopic
from learning_hub.models.enums import CloseReason


class SubjectTopicRepository:
    """Repository for SubjectTopic CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        subject_id: int,
        description: str,
    ) -> SubjectTopic:
        """Create a new topic."""
        topic = SubjectTopic(
            subject_id=subject_id,
            description=description,
        )
        self.session.add(topic)
        await self.session.commit()
        await self.session.refresh(topic)
        return topic

    async def get_or_create(
        self,
        subject_id: int,
        description: str,
    ) -> tuple[SubjectTopic, bool]:
        """Get existing topic or create new one.

        Returns:
            Tuple of (topic, created). created is True if new topic was created.
        """
        query = select(SubjectTopic).where(
            SubjectTopic.subject_id == subject_id,
            SubjectTopic.description == description,
        )
        result = await self.session.execute(query)
        topic = result.scalar_one_or_none()

        if topic is not None:
            return topic, False

        topic = SubjectTopic(
            subject_id=subject_id,
            description=description,
        )
        self.session.add(topic)
        await self.session.commit()
        await self.session.refresh(topic)
        return topic, True

    async def get_by_id(self, topic_id: int) -> SubjectTopic | None:
        """Get topic by ID."""
        return await self.session.get(SubjectTopic, topic_id)

    async def list(
        self,
        subject_id: int | None = None,
        is_open: bool | None = None,
    ) -> list[SubjectTopic]:
        """List topics with optional filters."""
        query = select(SubjectTopic)

        if subject_id is not None:
            query = query.where(SubjectTopic.subject_id == subject_id)

        if is_open is not None:
            if is_open:
                query = query.where(SubjectTopic.closed_at.is_(None))
            else:
                query = query.where(SubjectTopic.closed_at.is_not(None))

        query = query.order_by(SubjectTopic.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def close(
        self,
        topic_id: int,
        reason: CloseReason,
    ) -> SubjectTopic | None:
        """Close a topic with given reason. Returns None if not found."""
        topic = await self.get_by_id(topic_id)
        if topic is None:
            return None

        topic.closed_at = datetime.now()
        topic.close_reason = reason

        await self.session.commit()
        await self.session.refresh(topic)
        return topic
