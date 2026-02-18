"""SubjectTopic tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import CloseReason
from learning_hub.repositories.subject_topic import SubjectTopicRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_TOPIC,
    TOOL_LIST_TOPICS,
    TOOL_CLOSE_TOPIC,
)
from learning_hub.utils import dt_to_str


class SubjectTopicResponse(BaseModel):
    """SubjectTopic response schema."""
    id: int
    subject_id: int
    description: str
    created_at: str | None
    closed_at: str | None
    close_reason: str | None


def register_subject_topic_tools(mcp: FastMCP) -> None:
    """Register subject topic-related tools."""

    close_reason_options = ", ".join(f'"{r.value}"' for r in CloseReason)

    @mcp.tool(name=TOOL_CREATE_TOPIC, description="""Create a new subject topic.

    Args:
        subject_id: ID of the subject this topic belongs to
        description: Topic description

    Returns:
        Created topic
    """)
    async def create_topic(
        subject_id: int,
        description: str,
    ) -> SubjectTopicResponse:
        async with AsyncSessionLocal() as session:
            repo = SubjectTopicRepository(session)
            topic = await repo.create(
                subject_id=subject_id,
                description=description,
            )
            return SubjectTopicResponse(
                id=topic.id,
                subject_id=topic.subject_id,
                description=topic.description,
                created_at=dt_to_str(topic.created_at),
                closed_at=None,
                close_reason=None,
            )

    @mcp.tool(name=TOOL_LIST_TOPICS, description="""List subject topics.

    Args:
        subject_id: Filter by subject ID (optional)
        is_open: Filter by open/closed status - true for open, false for closed (optional)

    Returns:
        List of topics
    """)
    async def list_topics(
        subject_id: int | None = None,
        is_open: bool | None = None,
    ) -> list[SubjectTopicResponse]:
        async with AsyncSessionLocal() as session:
            repo = SubjectTopicRepository(session)
            topics = await repo.list(subject_id=subject_id, is_open=is_open)
            return [
                SubjectTopicResponse(
                    id=t.id,
                    subject_id=t.subject_id,
                    description=t.description,
                    created_at=dt_to_str(t.created_at),
                    closed_at=dt_to_str(t.closed_at),
                    close_reason=t.close_reason.value if t.close_reason else None,
                )
                for t in topics
            ]

    @mcp.tool(name=TOOL_CLOSE_TOPIC, description=f"""Close a subject topic.

    Args:
        topic_id: ID of the topic to close
        reason: Close reason - one of: {close_reason_options}

    Returns:
        Closed topic or null if not found
    """)
    async def close_topic(
        topic_id: int,
        reason: str,
    ) -> SubjectTopicResponse | None:
        reason_enum = CloseReason(reason)

        async with AsyncSessionLocal() as session:
            repo = SubjectTopicRepository(session)
            topic = await repo.close(topic_id=topic_id, reason=reason_enum)
            if topic is None:
                return None
            return SubjectTopicResponse(
                id=topic.id,
                subject_id=topic.subject_id,
                description=topic.description,
                created_at=dt_to_str(topic.created_at),
                closed_at=dt_to_str(topic.closed_at),
                close_reason=topic.close_reason.value if topic.close_reason else None,
            )
