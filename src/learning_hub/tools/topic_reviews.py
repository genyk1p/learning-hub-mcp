"""TopicReview tools for MCP server."""

import random
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import ReviewSource, TopicReviewStatus
from learning_hub.models.topic_review import TopicReview
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.tools.tool_names import (
    TOOL_LIST_TOPIC_REVIEWS,
    TOOL_MARK_TOPIC_REINFORCED,
    TOOL_GET_PENDING_REVIEWS_FOR_TOPIC,
    TOOL_INCREMENT_TOPIC_REPEAT_COUNT,
    TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW,
    TOOL_UPDATE_SUBJECT,
)
from learning_hub.utils import dt_to_str

EXTRA_PRACTICE_LOOKBACK_DAYS = 30


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
    review_source: str | None = None
    agent_note: str | None = None
    created_at: str | None
    updated_at: str | None


def _review_to_response(
    review: TopicReview,
    review_source: str | None = None,
) -> TopicReviewResponse:
    """Convert a TopicReview ORM object to response schema.

    Caller must ensure grade, subject, and subject_topic
    are eagerly loaded on the review instance.
    """
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
        review_source=review_source,
        created_at=dt_to_str(review.created_at),
        updated_at=dt_to_str(review.updated_at),
    )


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
            return [_review_to_response(r) for r in reviews]

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
            return _review_to_response(review)

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
            return [_review_to_response(r) for r in reviews]

    @mcp.tool(name=TOOL_GET_PRIORITY_TOPIC_FOR_REVIEW, description="""Get a high-priority pending topic for review.

    Picks from the top 4 priority candidates randomly to add variety.
    Priority: worse grade > fewer repeats > more recent.

    Use this for bonus task topic selection.

    Returns:
        A topic review with full context, or null if none pending.
        The `review_source` field indicates how the topic was selected:
        - "reinforcement" — standard pending TopicReview (topic needs reinforcement)
        - "extra_practice" — all reviews done, topic picked from recent grades
          (student wants to keep learning — praise them!)
    """)
    async def get_priority_topic_for_review() -> TopicReviewResponse | None:
        async with AsyncSessionLocal() as session:
            # Wave 1: pending TopicReviews
            repo = TopicReviewRepository(session)
            candidates = await repo.get_top_priority_candidates(limit=4)
            if candidates:
                review = random.choice(candidates)
                return _review_to_response(
                    review,
                    review_source=ReviewSource.REINFORCEMENT.value,
                )

            # Wave 2: no pending reviews — pick from recent grades
            grade_repo = GradeRepository(session)
            since = datetime.now() - timedelta(days=EXTRA_PRACTICE_LOOKBACK_DAYS)
            grades = await grade_repo.list_with_topics_since(since)
            if not grades:
                return None

            # Try favorite subjects first
            subject_repo = SubjectRepository(session)
            favorites = await subject_repo.list_favorites()
            favorite_ids = {s.id for s in favorites}

            agent_note = None
            if favorite_ids:
                # Scenario A: pick from favorite subjects
                favorite_grades = [g for g in grades if g.subject_id in favorite_ids]
                if favorite_grades:
                    grade = random.choice(favorite_grades)
                else:
                    # Favorites exist but have no graded topics in last 30 days
                    grade = random.choice(grades)
            else:
                # Scenario B: no favorites configured — random topic + note for agent
                grade = random.choice(grades)
                agent_note = (
                    f"No favorite subjects are configured. "
                    f"The topic was selected randomly — this is normal, "
                    f"do NOT inform the student about this.\n\n"
                    f"ACTION REQUIRED: Send a message to the system administrator "
                    f"via an available channel recommending to set up favorite subjects "
                    f"using the `{TOOL_UPDATE_SUBJECT}` tool with parameter "
                    f"`is_favorite=True` (maximum 3 favorites allowed).\n\n"
                    f"WHY: Favorite subjects are used by the system to generate "
                    f"advanced practice tasks when all pending reviews are done. "
                    f"This helps the student grow stronger in subjects they enjoy.\n\n"
                    f"IMPORTANT: Favorites should be chosen thoughtfully — "
                    f"there is no point in marking subjects like PE or Music "
                    f"as favorites, because Learning Hub cannot generate meaningful "
                    f"educational content for such subjects."
                )

            return TopicReviewResponse(
                id=0,
                subject_id=grade.subject_id,
                subject_topic_id=grade.subject_topic_id,
                grade_id=grade.id,
                status=ReviewSource.EXTRA_PRACTICE.value,
                repeat_count=0,
                grade_value=grade.grade_value.value,
                grade_date=dt_to_str(grade.date),
                subject_name=grade.subject.name,
                topic_description=grade.subject_topic.description,
                review_source=ReviewSource.EXTRA_PRACTICE.value,
                agent_note=agent_note,
                created_at=None,
                updated_at=None,
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
            return _review_to_response(review)
