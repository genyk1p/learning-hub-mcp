"""Tests for check_system_readiness logic."""

import pytest

from learning_hub.models.config_entry import ConfigEntry
from learning_hub.models.family_member import FamilyMember
from learning_hub.models.school import School
from learning_hub.repositories.config_entry import ConfigEntryRepository
from learning_hub.repositories.family_member import FamilyMemberRepository
from learning_hub.repositories.school import SchoolRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _add_admin(session, name="Dad"):
    member = FamilyMember(name=name, role="parent", is_admin=True)
    session.add(member)
    await session.commit()
    return member


async def _add_student(session, name="Stas", birth_date="2012-05-15"):
    from datetime import date
    member = FamilyMember(
        name=name, role="student", is_student=True,
        full_name=f"{name} Test",
        birth_date=date.fromisoformat(birth_date),
    )
    session.add(member)
    await session.commit()
    return member


async def _add_active_school(session, code="CZ", name="Czech School"):
    school = School(code=code, name=name, is_active=True)
    session.add(school)
    await session.commit()
    return school


async def _add_required_configs(session):
    """Add all required config entries with values set."""
    required = [
        ("TEMP_BOOK_DIR", "/tmp/books"),
        ("BOOKS_STORAGE_DIR", "/data/books"),
        ("ISSUES_LOG", "/data/issues.log"),
        ("FAMILY_LANGUAGE", "ru"),
    ]
    for key, value in required:
        entry = ConfigEntry(key=key, value=value, is_required=True, description=f"{key}")
        session.add(entry)
    await session.commit()


async def _check_readiness(session) -> tuple[bool, list]:
    """Run readiness checks manually (same logic as the tool)."""
    issues = []

    family_repo = FamilyMemberRepository(session)
    all_members = await family_repo.list()
    admins = [m for m in all_members if m.is_admin]
    students = [m for m in all_members if m.is_student]

    if not admins:
        issues.append("admin_member")

    if len(students) == 0:
        issues.append("student_member")
    elif len(students) > 1:
        issues.append("student_member_multiple")

    if len(students) == 1 and students[0].birth_date is None:
        issues.append("student_birth_date")

    school_repo = SchoolRepository(session)
    active_schools = await school_repo.list(is_active=True)
    if not active_schools:
        issues.append("active_school")

    config_repo = ConfigEntryRepository(session)
    unset = await config_repo.list_required_unset()
    for entry in unset:
        issues.append(f"required_config:{entry.key}")

    return len(issues) == 0, issues


# ---- tests ----


async def test_fully_configured_system_is_ready(session):
    """System is ready when admin, student, school, and configs are set."""
    await _add_admin(session)
    await _add_student(session)
    await _add_active_school(session)
    await _add_required_configs(session)

    ready, issues = await _check_readiness(session)
    assert ready is True
    assert issues == []


async def test_missing_admin(session):
    """System is not ready without an admin."""
    await _add_student(session)
    await _add_active_school(session)
    await _add_required_configs(session)

    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "admin_member" in issues


async def test_missing_student(session):
    """System is not ready without a student."""
    await _add_admin(session)
    await _add_active_school(session)
    await _add_required_configs(session)

    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "student_member" in issues


async def test_missing_active_school(session):
    """System is not ready without an active school."""
    await _add_admin(session)
    await _add_student(session)
    await _add_required_configs(session)

    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "active_school" in issues


async def test_missing_required_config(session):
    """System is not ready when required configs are unset."""
    await _add_admin(session)
    await _add_student(session)
    await _add_active_school(session)
    # Add required config WITHOUT value
    entry = ConfigEntry(key="FAMILY_LANGUAGE", value=None, is_required=True, description="Lang")
    session.add(entry)
    await session.commit()

    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "required_config:FAMILY_LANGUAGE" in issues


async def test_student_without_birth_date(session):
    """System flags student without birth_date."""
    await _add_admin(session)
    await _add_active_school(session)
    await _add_required_configs(session)
    # Student without birth_date
    member = FamilyMember(
        name="Stas", role="student", is_student=True, full_name="Stas Test",
    )
    session.add(member)
    await session.commit()

    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "student_birth_date" in issues


async def test_empty_system_has_multiple_issues(session):
    """Completely empty system has multiple issues."""
    ready, issues = await _check_readiness(session)
    assert ready is False
    assert "admin_member" in issues
    assert "student_member" in issues
    assert "active_school" in issues
