"""Repository for Gateway model."""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.gateway import Gateway
from learning_hub.models.enums import ChannelType


class GatewayRepository:
    """Repository for Gateway CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        family_member_id: int,
        channel: ChannelType,
        channel_uid: str,
        label: str | None = None,
        is_default: bool = False,
    ) -> Gateway:
        """Create a new gateway for a family member.

        If this is the first gateway for the member, is_default is set to True
        regardless of the provided value.
        """
        # Auto-set is_default=True if member has no gateways yet
        count_query = select(func.count()).where(
            Gateway.family_member_id == family_member_id
        ).select_from(Gateway)
        result = await self.session.execute(count_query)
        existing_count = result.scalar_one()

        if existing_count == 0:
            is_default = True

        gateway = Gateway(
            family_member_id=family_member_id,
            channel=channel,
            channel_uid=channel_uid,
            label=label,
            is_default=is_default,
        )
        self.session.add(gateway)
        await self.session.commit()
        await self.session.refresh(gateway)
        return gateway

    async def get_by_id(self, gateway_id: int) -> Gateway | None:
        """Get gateway by ID."""
        return await self.session.get(Gateway, gateway_id)

    async def lookup(
        self, channel: ChannelType, channel_uid: str
    ) -> Gateway | None:
        """Lookup gateway by channel + channel_uid. Eagerly loads family_member."""
        query = (
            select(Gateway)
            .options(joinedload(Gateway.family_member))
            .where(Gateway.channel == channel, Gateway.channel_uid == channel_uid)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_default(self, family_member_id: int) -> Gateway | None:
        """Get the default gateway for a family member."""
        query = select(Gateway).where(
            Gateway.family_member_id == family_member_id,
            Gateway.is_default.is_(True),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        family_member_id: int | None = None,
        channel: ChannelType | None = None,
    ) -> list[Gateway]:
        """List gateways with optional filters."""
        query = select(Gateway)

        if family_member_id is not None:
            query = query.where(Gateway.family_member_id == family_member_id)

        if channel is not None:
            query = query.where(Gateway.channel == channel)

        query = query.order_by(Gateway.family_member_id, Gateway.channel)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        gateway_id: int,
        channel_uid: str | None = None,
        label: str | None = None,
        clear_label: bool = False,
        is_default: bool | None = None,
    ) -> Gateway | None:
        """Update gateway fields. Returns None if not found."""
        gateway = await self.get_by_id(gateway_id)
        if gateway is None:
            return None

        if channel_uid is not None:
            gateway.channel_uid = channel_uid
        if clear_label:
            gateway.label = None
        elif label is not None:
            gateway.label = label
        if is_default is not None:
            gateway.is_default = is_default

        await self.session.commit()
        await self.session.refresh(gateway)
        return gateway

    async def delete(self, gateway_id: int) -> bool:
        """Delete a gateway. Returns True if deleted, False if not found."""
        gateway = await self.get_by_id(gateway_id)
        if gateway is None:
            return False

        await self.session.delete(gateway)
        await self.session.commit()
        return True
