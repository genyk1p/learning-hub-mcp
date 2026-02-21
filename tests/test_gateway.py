"""Tests for Gateway model and repository."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from learning_hub.models.enums import FamilyRole, ChannelType
from learning_hub.repositories.family_member import FamilyMemberRepository
from learning_hub.repositories.gateway import GatewayRepository


pytestmark = pytest.mark.asyncio


async def _create_member(session, name="Evhen", role=FamilyRole.ADMIN, **kwargs):
    """Helper to create a family member."""
    repo = FamilyMemberRepository(session)
    return await repo.create(name=name, role=role, **kwargs)


async def test_create_gateway(session):
    member = await _create_member(session)
    repo = GatewayRepository(session)

    gw = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="771706548",
    )

    assert gw.id is not None
    assert gw.channel == ChannelType.TELEGRAM
    assert gw.channel_uid == "771706548"
    assert gw.family_member_id == member.id


async def test_first_gateway_auto_default(session):
    """First gateway for a member should automatically become default."""
    member = await _create_member(session)
    repo = GatewayRepository(session)

    gw = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )

    assert gw.is_default is True


async def test_second_gateway_not_auto_default(session):
    """Second gateway should not be auto-default."""
    member = await _create_member(session)
    repo = GatewayRepository(session)

    await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )
    gw2 = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.WHATSAPP,
        channel_uid="+420123456",
    )

    assert gw2.is_default is False


async def test_lookup(session):
    """Lookup should return gateway with eagerly loaded family member."""
    member = await _create_member(
        session, name="Stas", role=FamilyRole.STUDENT,
        is_student=True, birth_date=date(2014, 5, 15),
    )
    repo = GatewayRepository(session)
    await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="5712222032",
    )

    found = await repo.lookup(channel=ChannelType.TELEGRAM, channel_uid="5712222032")

    assert found is not None
    assert found.family_member.name == "Stas"
    assert found.family_member.role == FamilyRole.STUDENT
    assert found.family_member.is_student is True


async def test_lookup_not_found(session):
    repo = GatewayRepository(session)
    found = await repo.lookup(channel=ChannelType.TELEGRAM, channel_uid="nonexistent")
    assert found is None


async def test_get_default(session):
    member = await _create_member(session)
    repo = GatewayRepository(session)

    await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )

    default = await repo.get_default(member.id)
    assert default is not None
    assert default.is_default is True
    assert default.channel == ChannelType.TELEGRAM


async def test_list_filter_by_member(session):
    m1 = await _create_member(session, name="Evhen")
    m2 = await _create_member(session, name="Tanya", role=FamilyRole.PARENT)
    repo = GatewayRepository(session)

    await repo.create(family_member_id=m1.id, channel=ChannelType.TELEGRAM, channel_uid="111")
    await repo.create(family_member_id=m1.id, channel=ChannelType.WHATSAPP, channel_uid="+111")
    await repo.create(family_member_id=m2.id, channel=ChannelType.TELEGRAM, channel_uid="222")

    gws = await repo.list(family_member_id=m1.id)
    assert len(gws) == 2


async def test_list_filter_by_channel(session):
    m1 = await _create_member(session, name="Evhen")
    m2 = await _create_member(session, name="Tanya", role=FamilyRole.PARENT)
    repo = GatewayRepository(session)

    await repo.create(family_member_id=m1.id, channel=ChannelType.TELEGRAM, channel_uid="111")
    await repo.create(family_member_id=m2.id, channel=ChannelType.TELEGRAM, channel_uid="222")
    await repo.create(family_member_id=m1.id, channel=ChannelType.WHATSAPP, channel_uid="+111")

    telegram_gws = await repo.list(channel=ChannelType.TELEGRAM)
    assert len(telegram_gws) == 2


async def test_update(session):
    member = await _create_member(session)
    repo = GatewayRepository(session)

    gw = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )

    updated = await repo.update(gw.id, label="personal")
    assert updated.label == "personal"


async def test_update_clear_label(session):
    member = await _create_member(session)
    repo = GatewayRepository(session)

    gw = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
        label="old",
    )

    updated = await repo.update(gw.id, clear_label=True)
    assert updated.label is None


async def test_update_not_found(session):
    repo = GatewayRepository(session)
    result = await repo.update(999, label="test")
    assert result is None


async def test_delete(session):
    member = await _create_member(session)
    repo = GatewayRepository(session)

    gw = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )

    deleted = await repo.delete(gw.id)
    assert deleted is True

    found = await repo.get_by_id(gw.id)
    assert found is None


async def test_delete_not_found(session):
    repo = GatewayRepository(session)
    deleted = await repo.delete(999)
    assert deleted is False


async def test_cascade_delete_member(session):
    """Deleting a family member should cascade-delete their gateways."""
    fm_repo = FamilyMemberRepository(session)
    gw_repo = GatewayRepository(session)

    member = await fm_repo.create(name="Test", role=FamilyRole.RELATIVE)
    await gw_repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="cascade_test",
    )

    await fm_repo.delete(member.id)

    found = await gw_repo.lookup(channel=ChannelType.TELEGRAM, channel_uid="cascade_test")
    assert found is None


# --- Constraint tests ---


async def test_constraint_unique_channel_uid(session):
    """Same channel + channel_uid cannot belong to two different members."""
    m1 = await _create_member(session, name="Evhen")
    m2 = await _create_member(session, name="Tanya", role=FamilyRole.PARENT)
    repo = GatewayRepository(session)

    await repo.create(
        family_member_id=m1.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="shared_id",
    )

    with pytest.raises(IntegrityError):
        await repo.create(
            family_member_id=m2.id,
            channel=ChannelType.TELEGRAM,
            channel_uid="shared_id",
        )


async def test_same_uid_different_channels_allowed(session):
    """Same channel_uid on different channels should be fine."""
    member = await _create_member(session)
    repo = GatewayRepository(session)

    await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="12345",
    )
    gw2 = await repo.create(
        family_member_id=member.id,
        channel=ChannelType.DISCORD,
        channel_uid="12345",
    )

    assert gw2.id is not None


async def test_constraint_single_default_per_member(session):
    """Only one default gateway per member is allowed."""
    member = await _create_member(session)
    repo = GatewayRepository(session)

    # First one auto-defaults
    await repo.create(
        family_member_id=member.id,
        channel=ChannelType.TELEGRAM,
        channel_uid="111",
    )

    with pytest.raises(IntegrityError):
        await repo.create(
            family_member_id=member.id,
            channel=ChannelType.WHATSAPP,
            channel_uid="+111",
            is_default=True,
        )
