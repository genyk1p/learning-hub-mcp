"""TopicReview tools for MCP server."""

import random

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import TopicReviewStatus
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.tools.tool_names import (
    TOOL_LIST_TOPIC_REVIEWS,
    TOOL_MARK_TOPIC_REINFORCED,
    TOOL_GET_PENDING_REVIEWS_FOR_TOPIC,
    TOOL_INCREMENT_TOPIC_REPEAT_COUNT,
    TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW,
)
from learning_hub.utils import dt_to_str


class TopicReviewResponse(BaseModel):
    """TopicReview response schema."""
    id: int
    subject_id: int
    subject_topic_id: int
    grade_id: int
    status: str
    repeat_count: int
    grade_value: int
    grade_date: str | None
    subject_name: str
    topic_description: str
    created_at: str | None
    updated_at: str | None


def register_topic_review_tools(mcp: FastMCP) -> None:
    """Register topic review related tools."""

    status_options = ", ".join(f'"{s.value}"' for s in TopicReviewStatus)

    @mcp.tool(name=TOOL_LIST_TOPIC_REVIEWS, description=f"""List topic reviews (topics that need reinforcement).

    Topic reviews are created automatically when syncing grades > 1 from EduPage.
    Shows topics where student needs additional practice.

    Args:
        subject_id: Filter by subject ID (optional)
        subject_topic_id: Filter by topic ID (optional)
        status: Filter by status - one of: {status_options} (optional)

    Returns:
        List of topic reviews
    """)
    async def list_topic_reviews(
        subject_id: int | None = None,
        subject_topic_id: int | None = None,
        status: str | None = None,
    ) -> list[TopicReviewResponse]:
        status_enum = TopicReviewStatus(status) if status else None

        async with AsyncSessionLocal() as session:
            repo = TopicReviewRepository(session)
            reviews = await repo.list(
                subject_id=subject_id,
                subject_topic_id=subject_topic_id,
                status=status_enum,
            )
            return [
                TopicReviewResponse(
                    id=r.id,
                    subject_id=r.subject_id,
                    subject_topic_id=r.subject_topic_id,
                    grade_id=r.grade_id,
                    status=r.status.value,
                    repeat_count=r.repeat_count,
                    grade_value=r.grade.grade_value.value,
                    grade_date=dt_to_str(r.grade.date),
                    subject_name=r.subject.name,
                    topic_description=r.subject_topic.description,
                    created_at=dt_to_str(r.created_at),
                    updated_at=dt_to_str(r.updated_at),
                )
                for r in reviews
            ]

    @mcp.tool(name=TOOL_MARK_TOPIC_REINFORCED, description="""Mark topic review as reinforced.

    Use this when the topic has been sufficiently practiced through bonus tasks.

    Args:
        review_id: ID of the topic review to mark as reinforced

    Returns:
        Updated topic review or null if not found
    """)
    async def mark_topic_reinforced(review_id: int) -> TopicReviewResponse | None:
        async with AsyncSessionLocal() as session:
            repo = TopicReviewRepository(session)
            review = await repo.mark_reinforced(review_id)
            if review is None:
                return None
            return TopicReviewResponse(
                id=review.id,
                subject_id=review.subject_id,
                subject_topic_id=review.subject_topic_id,
                grade_id=review.grade_id,
                status=review.status.value,
                repeat_count=review.repeat_count,
                grade_value=review.grade.grade_value.value,
                grade_date=dt_to_str(review.grade.date),
                subject_name=review.subject.name,
                topic_description=review.subject_topic.description,
                created_at=dt_to_str(review.created_at),
                updated_at=dt_to_str(review.updated_at),
            )

    @mcp.tool(name=TOOL_GET_PENDING_REVIEWS_FOR_TOPIC, description="""Get pending topic reviews for a subject topic.

    Use this to find what needs reinforcement for a specific topic,
    e.g. after completing a bonus task linked to that topic.

    Args:
        subject_topic_id: ID of the subject topic

    Returns:
        List of pending topic reviews for this topic
    """)
    async def get_pending_reviews_for_topic(
        subject_topic_id: int,
    ) -> list[TopicReviewResponse]:
        async with AsyncSessionLocal() as session:
            repo = TopicReviewRepository(session)
            reviews = await repo.list(
                subject_topic_id=subject_topic_id,
                status=TopicReviewStatus.PENDING,
            )
            return [
                TopicReviewResponse(
                    id=r.id,
                    subject_id=r.subject_id,
                    subject_topic_id=r.subject_topic_id,
                    grade_id=r.grade_id,
                    status=r.status.value,
                    repeat_count=r.repeat_count,
                    grade_value=r.grade.grade_value.value,
                    grade_date=dt_to_str(r.grade.date),
                    subject_name=r.subject.name,
                    topic_description=r.subject_topic.description,
                    created_at=dt_to_str(r.created_at),
                    updated_at=dt_to_str(r.updated_at),
                )
                for r in reviews
            ]

    @mcp.tool(name=TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW, description="""Get a high-priority pending topic for review.

    Picks from the top 4 priority candidates randomly to add variety.
    Priority: worse grade > fewer repeats > more recent.

    Use this for bonus task topic selection.

    Returns:
        A topic review with full context, or null if none pending
    """)
    async def get_priority_topic_for_review() -> TopicReviewResponse | None:
        async with AsyncSessionLocal() as session:
            repo = TopicReviewRepository(session)
            candidates = await repo.get_top_priority_candidates(limit=4)
            if not candidates:
                return None
            review = random.choice(candidates)
            return TopicReviewResponse(
                id=review.id,
                subject_id=review.subject_id,
                subject_topic_id=review.subject_topic_id,
                grade_id=review.grade_id,
                status=review.status.value,
                repeat_count=review.repeat_count,
                grade_value=review.grade.grade_value.value,
                grade_date=dt_to_str(review.grade.date),
                subject_name=review.subject.name,
                topic_description=review.subject_topic.description,
                created_at=dt_to_str(review.created_at),
                updated_at=dt_to_str(review.updated_at),
            )

    @mcp.tool(name=TOOL_INCREMENT_TOPIC_REPEAT_COUNT, description="""Increment repeat count for a topic review.

    Call this when a bonus task related to the topic is completed.

    Args:
        review_id: ID of the topic review

    Returns:
        Updated topic review or null if not found
    """)
    async def increment_topic_repeat_count(review_id: int) -> TopicReviewResponse | None:
        async with AsyncSessionLocal() as session:
            repo = TopicReviewRepository(session)
            review = await repo.increment_repeat_count(review_id)
            if review is None:
                return None
            return TopicReviewResponse(
                id=review.id,
                subject_id=review.subject_id,
                subject_topic_id=review.subject_topic_id,
                grade_id=review.grade_id,
                status=review.status.value,
                repeat_count=review.repeat_count,
                grade_value=review.grade.grade_value.value,
                grade_date=dt_to_str(review.grade.date),
                subject_name=review.subject.name,
                topic_description=review.subject_topic.description,
                created_at=dt_to_str(review.created_at),
                updated_at=dt_to_str(review.updated_at),
            )
