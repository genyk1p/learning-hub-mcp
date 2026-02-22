"""Tests for SyncProvider model and repository."""

import pytest

from learning_hub.models.enums import SyncProviderType
from learning_hub.models.school import School
from learning_hub.models.sync_provider import SyncProvider
from learning_hub.repositories.sync_provider import SyncProviderRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _create_school(session, code="CZ", name="Czech School") -> School:
    """Create a school and return it."""
    school = School(code=code, name=name, is_active=True)
    session.add(school)
    await session.commit()
    await session.refresh(school)
    return school


async def _seed_provider(session, code="edupage", name="EduPage") -> SyncProvider:
    """Seed a sync provider (mimics migration behavior)."""
    provider = SyncProvider(code=code, name=name, is_active=False)
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


# ---- enum ↔ DB sync tests ----


async def test_all_enum_values_have_db_rows(session):
    """Every SyncProviderType enum value must have a row in the DB.

    This catches the case where someone adds a new enum value
    but forgets to create a migration to seed the row.
    """
    # Seed all providers (mimics what migrations do)
    for pt in SyncProviderType:
        await _seed_provider(session, code=pt.value, name=pt.value)

    repo = SyncProviderRepository(session)
    all_providers = await repo.list_all()
    db_codes = {p.code for p in all_providers}

    for pt in SyncProviderType:
        assert pt.value in db_codes, (
            f"SyncProviderType.{pt.name} ({pt.value}) has no row in sync_providers. "
            f"Add a migration to seed it."
        )


async def test_db_rows_match_enum_values(session):
    """Every DB row code must be a valid SyncProviderType enum value.

    This catches the case where a DB row exists but the enum
    value was removed or renamed.
    """
    for pt in SyncProviderType:
        await _seed_provider(session, code=pt.value, name=pt.value)

    repo = SyncProviderRepository(session)
    all_providers = await repo.list_all()
    enum_values = {pt.value for pt in SyncProviderType}

    for provider in all_providers:
        assert provider.code in enum_values, (
            f"sync_providers row code='{provider.code}' is not in SyncProviderType enum. "
            f"Either add it to the enum or remove the DB row."
        )


# ---- CRUD tests ----


async def test_get_by_code(session):
    """Can retrieve provider by code."""
    await _seed_provider(session)
    repo = SyncProviderRepository(session)

    provider = await repo.get_by_code("edupage")
    assert provider is not None
    assert provider.code == "edupage"
    assert provider.name == "EduPage"
    assert provider.is_active is False
    assert provider.school_id is None


async def test_get_by_code_not_found(session):
    """Returns None for unknown code."""
    repo = SyncProviderRepository(session)
    assert await repo.get_by_code("nonexistent") is None


async def test_link_school_and_activate(session):
    """Can link a school and activate the provider."""
    school = await _create_school(session)
    await _seed_provider(session)
    repo = SyncProviderRepository(session)

    provider = await repo.get_by_code("edupage")
    updated = await repo.update(
        provider_id=provider.id,
        school_id=school.id,
        is_active=True,
    )

    assert updated.is_active is True
    assert updated.school_id == school.id
    assert updated.school is not None
    assert updated.school.code == "CZ"


async def test_activate_without_school_raises(session):
    """Activating a provider without a linked school raises ValueError."""
    await _seed_provider(session)
    repo = SyncProviderRepository(session)

    provider = await repo.get_by_code("edupage")
    with pytest.raises(ValueError, match="without a linked school"):
        await repo.update(provider_id=provider.id, is_active=True)


async def test_clear_school(session):
    """Can unlink a school using clear_school flag."""
    school = await _create_school(session)
    await _seed_provider(session)
    repo = SyncProviderRepository(session)

    provider = await repo.get_by_code("edupage")
    await repo.update(
        provider_id=provider.id, school_id=school.id
    )
    updated = await repo.update(
        provider_id=provider.id, clear_school=True
    )

    assert updated.school_id is None


async def test_unique_school_constraint(session):
    """Two providers cannot link to the same school."""
    from sqlalchemy.exc import IntegrityError

    school = await _create_school(session)
    await _seed_provider(session, code="edupage", name="EduPage")
    await _seed_provider(session, code="bakalari", name="Bakalari")
    repo = SyncProviderRepository(session)

    p1 = await repo.get_by_code("edupage")
    await repo.update(provider_id=p1.id, school_id=school.id)

    p2 = await repo.get_by_code("bakalari")
    with pytest.raises(IntegrityError):
        await repo.update(provider_id=p2.id, school_id=school.id)


async def test_list_all(session):
    """list_all returns all providers ordered by code."""
    await _seed_provider(session, code="edupage", name="EduPage")
    await _seed_provider(session, code="bakalari", name="Bakalari")
    repo = SyncProviderRepository(session)

    providers = await repo.list_all()
    assert len(providers) == 2
    assert providers[0].code == "bakalari"
    assert providers[1].code == "edupage"
