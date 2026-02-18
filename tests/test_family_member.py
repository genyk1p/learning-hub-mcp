"""Tests for FamilyMember model and repository."""

import pytest
from sqlalchemy.exc import IntegrityError

from learning_hub.models.enums import FamilyRole
from learning_hub.repositories.family_member import FamilyMemberRepository


pytestmark = pytest.mark.asyncio


async def test_create_family_member(session):
    repo = FamilyMemberRepository(session)
    member = await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)

    assert member.id is not None
    assert member.name == "Evhen"
    assert member.role == FamilyRole.ADMIN
    assert member.is_admin is True
    assert member.is_student is False


async def test_create_with_all_fields(session):
    repo = FamilyMemberRepository(session)
    member = await repo.create(
        name="Stas",
        role=FamilyRole.STUDENT,
        full_name="Stanislav Kukoba",
        is_student=True,
        notes="Student, born 2014",
    )

    assert member.full_name == "Stanislav Kukoba"
    assert member.is_student is True
    assert member.notes == "Student, born 2014"


async def test_get_by_id(session):
    repo = FamilyMemberRepository(session)
    created = await repo.create(name="Tanya", role=FamilyRole.PARENT)

    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.name == "Tanya"


async def test_get_by_id_not_found(session):
    repo = FamilyMemberRepository(session)
    found = await repo.get_by_id(999)
    assert found is None


async def test_get_student(session):
    repo = FamilyMemberRepository(session)
    await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)
    await repo.create(name="Stas", role=FamilyRole.STUDENT, is_student=True)

    student = await repo.get_student()
    assert student is not None
    assert student.name == "Stas"
    assert student.is_student is True


async def test_get_student_none(session):
    repo = FamilyMemberRepository(session)
    await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)

    student = await repo.get_student()
    assert student is None


async def test_list_all(session):
    repo = FamilyMemberRepository(session)
    await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)
    await repo.create(name="Natasha", role=FamilyRole.TUTOR)
    await repo.create(name="Stas", role=FamilyRole.STUDENT, is_student=True)

    members = await repo.list()
    assert len(members) == 3


async def test_list_filter_by_role(session):
    repo = FamilyMemberRepository(session)
    await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)
    await repo.create(name="Natasha", role=FamilyRole.TUTOR)
    await repo.create(name="Valentina", role=FamilyRole.TUTOR)

    tutors = await repo.list(role=FamilyRole.TUTOR)
    assert len(tutors) == 2
    assert all(m.role == FamilyRole.TUTOR for m in tutors)


async def test_update(session):
    repo = FamilyMemberRepository(session)
    member = await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)

    updated = await repo.update(member.id, full_name="Evhen Kukoba", notes="sudo")
    assert updated.full_name == "Evhen Kukoba"
    assert updated.notes == "sudo"


async def test_update_clear_notes(session):
    repo = FamilyMemberRepository(session)
    member = await repo.create(name="Evhen", role=FamilyRole.ADMIN, notes="old notes")

    updated = await repo.update(member.id, clear_notes=True)
    assert updated.notes is None


async def test_update_not_found(session):
    repo = FamilyMemberRepository(session)
    result = await repo.update(999, name="test")
    assert result is None


async def test_delete(session):
    repo = FamilyMemberRepository(session)
    member = await repo.create(name="Test", role=FamilyRole.RELATIVE)

    deleted = await repo.delete(member.id)
    assert deleted is True

    found = await repo.get_by_id(member.id)
    assert found is None


async def test_delete_not_found(session):
    repo = FamilyMemberRepository(session)
    deleted = await repo.delete(999)
    assert deleted is False


# --- Constraint tests ---


async def test_constraint_student_not_admin(session):
    """is_student=True and is_admin=True should be rejected."""
    repo = FamilyMemberRepository(session)
    with pytest.raises(IntegrityError):
        await repo.create(
            name="Bad", role=FamilyRole.STUDENT, is_student=True, is_admin=True
        )


async def test_constraint_single_student(session):
    """Only one member with is_student=True is allowed."""
    repo = FamilyMemberRepository(session)
    await repo.create(name="Stas", role=FamilyRole.STUDENT, is_student=True)

    with pytest.raises(IntegrityError):
        await repo.create(name="Other", role=FamilyRole.STUDENT, is_student=True)


async def test_multiple_non_students_allowed(session):
    """Multiple members with is_student=False should be fine."""
    repo = FamilyMemberRepository(session)
    await repo.create(name="Evhen", role=FamilyRole.ADMIN, is_admin=True)
    await repo.create(name="Tanya", role=FamilyRole.PARENT)
    await repo.create(name="Natasha", role=FamilyRole.TUTOR)
    await repo.create(name="Valentina", role=FamilyRole.TUTOR)
    await repo.create(name="Anatoliy", role=FamilyRole.RELATIVE)

    members = await repo.list()
    assert len(members) == 5
