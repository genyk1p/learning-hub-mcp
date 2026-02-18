"""Gateway tools for MCP server."""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import ChannelType
from learning_hub.repositories.gateway import GatewayRepository
from learning_hub.tools.tool_names import (
    TOOL_CREATE_GATEWAY,
    TOOL_LIST_GATEWAYS,
    TOOL_UPDATE_GATEWAY,
    TOOL_DELETE_GATEWAY,
    TOOL_LOOKUP_GATEWAY,
)
from learning_hub.utils import dt_to_str


class GatewayResponse(BaseModel):
    """Gateway response schema."""
    id: int
    family_member_id: int
    channel: str
    channel_uid: str
    label: str | None
    is_default: bool
    created_at: str | None
    updated_at: str | None


class GatewayLookupResponse(BaseModel):
    """Gateway lookup response with family member context."""
    gateway_id: int
    channel: str
    channel_uid: str
    is_default: bool
    member_id: int
    member_name: str
    member_role: str
    member_is_admin: bool
    member_is_student: bool


def _to_response(g) -> GatewayResponse:
    return GatewayResponse(
        id=g.id,
        family_member_id=g.family_member_id,
        channel=g.channel.value,
        channel_uid=g.channel_uid,
        label=g.label,
        is_default=g.is_default,
        created_at=dt_to_str(g.created_at),
        updated_at=dt_to_str(g.updated_at),
    )


def register_gateway_tools(mcp: FastMCP) -> None:
    """Register gateway related tools."""

    channel_options = ", ".join(f'"{c.value}"' for c in ChannelType)

    @mcp.tool(name=TOOL_CREATE_GATEWAY, description=f"""Create a new gateway (communication channel) for a family member.

    If this is the first gateway for the member, it becomes the default automatically.

    Args:
        family_member_id: ID of the family member
        channel: Channel type - one of: {channel_options}
        channel_uid: User's identifier on this channel (Telegram ID, phone number, etc.)
        label: Optional label ("personal", "work", etc.)
        is_default: Set as default channel for this member (default false)

    Returns:
        Created gateway
    """)
    async def create_gateway(
        family_member_id: int,
        channel: str,
        channel_uid: str,
        label: str | None = None,
        is_default: bool = False,
    ) -> GatewayResponse:
        channel_enum = ChannelType(channel)

        async with AsyncSessionLocal() as session:
            repo = GatewayRepository(session)
            gateway = await repo.create(
                family_member_id=family_member_id,
                channel=channel_enum,
                channel_uid=channel_uid,
                label=label,
                is_default=is_default,
            )
            return _to_response(gateway)

    @mcp.tool(name=TOOL_LIST_GATEWAYS, description=f"""List gateways.

    Args:
        family_member_id: Filter by family member ID (optional)
        channel: Filter by channel type - one of: {channel_options} (optional)

    Returns:
        List of gateways
    """)
    async def list_gateways(
        family_member_id: int | None = None,
        channel: str | None = None,
    ) -> list[GatewayResponse]:
        channel_enum = ChannelType(channel) if channel else None

        async with AsyncSessionLocal() as session:
            repo = GatewayRepository(session)
            gateways = await repo.list(
                family_member_id=family_member_id,
                channel=channel_enum,
            )
            return [_to_response(g) for g in gateways]

    @mcp.tool(name=TOOL_UPDATE_GATEWAY, description="""Update a gateway.

    Args:
        gateway_id: ID of the gateway to update
        channel_uid: New channel user ID (optional)
        label: New label (optional)
        clear_label: Set to true to remove label (optional)
        is_default: Set as default channel (optional)

    Returns:
        Updated gateway or null if not found
    """)
    async def update_gateway(
        gateway_id: int,
        channel_uid: str | None = None,
        label: str | None = None,
        clear_label: bool = False,
        is_default: bool | None = None,
    ) -> GatewayResponse | None:
        async with AsyncSessionLocal() as session:
            repo = GatewayRepository(session)
            gateway = await repo.update(
                gateway_id=gateway_id,
                channel_uid=channel_uid,
                label=label,
                clear_label=clear_label,
                is_default=is_default,
            )
            if gateway is None:
                return None
            return _to_response(gateway)

    @mcp.tool(name=TOOL_DELETE_GATEWAY, description="""Delete a gateway.

    Args:
        gateway_id: ID of the gateway to delete

    Returns:
        True if deleted, False if not found
    """)
    async def delete_gateway(gateway_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            repo = GatewayRepository(session)
            return await repo.delete(gateway_id)

    @mcp.tool(name=TOOL_LOOKUP_GATEWAY, description=f"""Look up a family member by their channel identity.

    Use this to identify who is sending a message. Returns the gateway
    with full family member context (name, role, permissions).

    Args:
        channel: Channel type - one of: {channel_options}
        channel_uid: User's identifier on this channel

    Returns:
        Gateway with family member info, or null if not found
    """)
    async def lookup_gateway(
        channel: str,
        channel_uid: str,
    ) -> GatewayLookupResponse | None:
        channel_enum = ChannelType(channel)

        async with AsyncSessionLocal() as session:
            repo = GatewayRepository(session)
            gateway = await repo.lookup(
                channel=channel_enum,
                channel_uid=channel_uid,
            )
            if gateway is None:
                return None
            m = gateway.family_member
            return GatewayLookupResponse(
                gateway_id=gateway.id,
                channel=gateway.channel.value,
                channel_uid=gateway.channel_uid,
                is_default=gateway.is_default,
                member_id=m.id,
                member_name=m.name,
                member_role=m.role.value,
                member_is_admin=m.is_admin,
                member_is_student=m.is_student,
            )
