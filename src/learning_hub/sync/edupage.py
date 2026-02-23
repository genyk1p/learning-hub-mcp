"""EduPage sync implementation.

Syncs grades and homeworks from EduPage API into the local database.
Called by the run_sync dispatcher — not exposed as a standalone MCP tool.
"""

import re
from datetime import datetime

from edupage_api import Edupage  # type: ignore[import-untyped]
from edupage_api.timeline import EventType  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.enums import (
    GradeSource,
    GradeValue,
    HomeworkStatus,
    SyncProviderType,
)
from learning_hub.models.sync_provider import SyncProvider
from learning_hub.repositories.family_member import FamilyMemberRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.repositories.secret import SecretRepository
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.repositories.subject_topic import SubjectTopicRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.sync.result import ProviderSyncResult
from learning_hub.tools.tool_names import (
    TOOL_CREATE_FAMILY_MEMBER,
    TOOL_RUN_SYNC,
    TOOL_SET_SECRET,
)


async def run_edupage_sync(
    session: AsyncSession,
    provider: SyncProvider,
) -> ProviderSyncResult:
    """Run full EduPage sync (grades + homeworks).

    Args:
        session: Active DB session (caller manages lifecycle).
        provider: SyncProvider with eager-loaded school.
            Caller guarantees is_active=True and school_id is set.

    Returns:
        ProviderSyncResult with combined stats.
    """
    school_id = provider.school_id
    school_name = provider.school.name if provider.school else None

    if school_id is None:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=["Provider has no school linked. Link a school first."],
        )

    errors: list[str] = []

    # Read credentials
    secret_repo = SecretRepository(session)
    username = await secret_repo.get_value("EDUPAGE_USERNAME")
    password = await secret_repo.get_value("EDUPAGE_PASSWORD")
    subdomain = await secret_repo.get_value("EDUPAGE_SUBDOMAIN")

    if not username or not password:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[
                "EduPage credentials not configured. "
                "Set EDUPAGE_USERNAME and EDUPAGE_PASSWORD via set_secret."
            ],
        )

    # Connect to EduPage
    ep = Edupage()
    try:
        if subdomain:
            ep.login(username, password, subdomain)
        else:
            ep.login_auto(username, password)
    except Exception as e:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[f"EduPage login failed: {e}"],
        )

    # Switch to child if student_id is configured (parent account)
    student_id = await secret_repo.get_value("EDUPAGE_STUDENT_ID")
    if student_id:
        try:
            student_id_int = int(student_id)
        except ValueError:
            return ProviderSyncResult(
                provider_code=provider.code,
                provider_name=provider.name,
                school_name=school_name,
                errors=[
                    f"EDUPAGE_STUDENT_ID value '{student_id}' is not a valid integer. "
                    f"Update it via {TOOL_SET_SECRET} with a numeric person_id."
                ],
            )
        try:
            ep.switch_to_child(student_id_int)
        except Exception as e:
            return ProviderSyncResult(
                provider_code=provider.code,
                provider_name=provider.name,
                school_name=school_name,
                errors=[
                    f"Failed to switch to child (EDUPAGE_STUDENT_ID={student_id}): {e}"
                ],
            )
    else:
        # No student_id configured — try to auto-match by full_name
        match_result = await _match_student_id(session, ep)
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[match_result],
        )

    # Fetch subjects for full names mapping
    try:
        edupage_subjects = ep.get_subjects()
        subject_names_by_id = {s.subject_id: s.name for s in edupage_subjects}
        subject_names_by_str = {str(s.subject_id): s.name for s in edupage_subjects}
    except Exception as e:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[f"Failed to fetch subjects: {e}"],
        )

    # --- Sync grades ---
    grades_result = await _sync_grades(
        session, ep, school_id, subject_names_by_id, errors
    )

    # --- Sync homeworks ---
    homeworks_result = await _sync_homeworks(
        session, ep, school_id, subject_names_by_str, errors
    )

    return ProviderSyncResult(
        provider_code=provider.code,
        provider_name=provider.name,
        school_name=school_name,
        grades_fetched=grades_result["grades_fetched"],
        grades_created=grades_result["grades_created"],
        grades_skipped=grades_result["grades_skipped"],
        homeworks_fetched=homeworks_result["homeworks_fetched"],
        homeworks_created=homeworks_result["homeworks_created"],
        homeworks_skipped=homeworks_result["homeworks_skipped"],
        subjects_created=(
            grades_result["subjects_created"]
            + homeworks_result["subjects_created"]
        ),
        topics_created=grades_result["topics_created"],
        reviews_created=grades_result["reviews_created"],
        errors=errors,
    )


async def _sync_grades(
    session: AsyncSession,
    ep: Edupage,
    school_id: int,
    subject_names: dict,
    errors: list[str],
) -> dict:
    """Sync grades from EduPage. Returns stats dict."""
    grades_created = 0
    grades_skipped = 0
    subjects_created = 0
    topics_created = 0
    reviews_created = 0

    try:
        edupage_grades = ep.get_grades()
    except Exception as e:
        errors.append(f"Failed to fetch grades: {e}")
        return {
            "grades_fetched": 0,
            "grades_created": 0,
            "grades_skipped": 0,
            "subjects_created": 0,
            "topics_created": 0,
            "reviews_created": 0,
        }

    subject_repo = SubjectRepository(session)
    topic_repo = SubjectTopicRepository(session)
    grade_repo = GradeRepository(session)
    review_repo = TopicReviewRepository(session)

    for eg in edupage_grades:
        # Check if already synced
        existing = await grade_repo.get_by_external_id(
            str(eg.event_id), SyncProviderType.EDUPAGE
        )
        if existing is not None:
            grades_skipped += 1
            continue

        # Parse grade value to int
        grade_int = _parse_grade_value(eg.grade_n)
        if grade_int is None:
            errors.append(f"Skipped non-numeric: {eg.subject_name} - {eg.grade_n}")
            grades_skipped += 1
            continue
        if grade_int < 1 or grade_int > 5:
            errors.append(f"Invalid grade {grade_int} for {eg.subject_name}")
            grades_skipped += 1
            continue

        grade_value = GradeValue(grade_int)

        # Find or create subject (use full name from subjects map)
        full_name = subject_names.get(eg.subject_id, eg.subject_name)
        subject, created = await subject_repo.get_or_create(
            school_id=school_id,
            name=full_name,
        )
        if created:
            subjects_created += 1

        # Find or create topic if title exists
        subject_topic_id = None
        topic_text = eg.title.strip() if eg.title else None
        if topic_text:
            topic, topic_created = await topic_repo.get_or_create(
                subject_id=subject.id,
                description=topic_text,
            )
            subject_topic_id = topic.id
            if topic_created:
                topics_created += 1

        # Create grade
        try:
            grade = await grade_repo.create(
                subject_id=subject.id,
                grade_value=grade_value,
                date=eg.date,
                subject_topic_id=subject_topic_id,
                external_id=str(eg.event_id),
                external_source=SyncProviderType.EDUPAGE,
                source=GradeSource.AUTO,
                original_value=str(eg.grade_n),
            )
            grades_created += 1

            # Create TopicReview for grades > 1 if topic exists
            if grade_int > 1 and subject_topic_id is not None:
                try:
                    await review_repo.create(
                        subject_id=subject.id,
                        subject_topic_id=subject_topic_id,
                        grade_id=grade.id,
                    )
                    reviews_created += 1
                except Exception as e:
                    errors.append(f"Failed to create topic review: {e}")
        except Exception as e:
            errors.append(f"Failed to create grade: {e}")

    return {
        "grades_fetched": len(edupage_grades),
        "grades_created": grades_created,
        "grades_skipped": grades_skipped,
        "subjects_created": subjects_created,
        "topics_created": topics_created,
        "reviews_created": reviews_created,
    }


async def _sync_homeworks(
    session: AsyncSession,
    ep: Edupage,
    school_id: int,
    subject_names: dict,
    errors: list[str],
) -> dict:
    """Sync homeworks from EduPage notifications. Returns stats dict."""
    homeworks_created = 0
    homeworks_skipped = 0
    subjects_created = 0

    try:
        notifications = ep.get_notifications()
        homework_events = [
            n for n in notifications
            if n.event_type == EventType.HOMEWORK
        ]
    except Exception as e:
        errors.append(f"Failed to fetch notifications: {e}")
        return {
            "homeworks_fetched": 0,
            "homeworks_created": 0,
            "homeworks_skipped": 0,
            "subjects_created": 0,
        }

    subject_repo = SubjectRepository(session)
    homework_repo = HomeworkRepository(session)

    for event in homework_events:
        data = event.additional_data
        if not data or not isinstance(data, dict):
            homeworks_skipped += 1
            continue

        edupage_id = data.get("id")
        if not edupage_id:
            homeworks_skipped += 1
            continue

        # Check if already synced
        existing = await homework_repo.get_by_external_id(
            edupage_id, SyncProviderType.EDUPAGE
        )
        if existing is not None:
            homeworks_skipped += 1
            continue

        # Get subject by predmetid
        predmet_id = data.get("predmetid")
        if not predmet_id:
            homeworks_skipped += 1
            continue
        full_name = subject_names.get(predmet_id)
        if not full_name:
            errors.append(
                f"Unknown subject {predmet_id} for homework {edupage_id}"
            )
            homeworks_skipped += 1
            continue

        subject, created = await subject_repo.get_or_create(
            school_id=school_id,
            name=full_name,
        )
        if created:
            subjects_created += 1

        # Parse deadline date
        deadline_str = data.get("date")
        deadline_at = None
        if deadline_str:
            try:
                deadline_at = datetime.strptime(deadline_str, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    f"Unparseable deadline '{deadline_str}' for homework "
                    f"{edupage_id} — saved without deadline."
                )

        # Check if deadline already passed - mark as done
        status = HomeworkStatus.PENDING
        if deadline_at and deadline_at < datetime.now():
            status = HomeworkStatus.DONE

        # Get description from nazov
        description = data.get("nazov", "").strip()
        if not description:
            description = event.text.strip() if event.text else "No description"

        try:
            await homework_repo.create(
                subject_id=subject.id,
                description=description,
                deadline_at=deadline_at,
                assigned_at=event.timestamp,
                external_id=edupage_id,
                external_source=SyncProviderType.EDUPAGE,
                status=status,
            )
            homeworks_created += 1
        except Exception as e:
            errors.append(f"Failed to create homework: {e}")

    return {
        "homeworks_fetched": len(homework_events),
        "homeworks_created": homeworks_created,
        "homeworks_skipped": homeworks_skipped,
        "subjects_created": subjects_created,
    }


async def _match_student_id(
    session: AsyncSession,
    ep: Edupage,
) -> str:
    """Try to auto-match student by full_name, or return error with student list.

    Always returns an error string — sync cannot proceed without EDUPAGE_STUDENT_ID.
    The caller should wrap this in a ProviderSyncResult and abort.
    """
    fm_repo = FamilyMemberRepository(session)
    student = await fm_repo.get_student()

    if student is None:
        return (
            "EDUPAGE_STUDENT_ID is not set and no student is registered in the system. "
            f"Create a student family member first via {TOOL_CREATE_FAMILY_MEMBER} "
            f"(with full_name set), then retry {TOOL_RUN_SYNC}."
        )

    student_full_name = (
        student.full_name.strip().lower()
        if student.full_name else None
    )

    try:
        edupage_students = ep.get_students()
    except Exception as e:
        return (
            f"EDUPAGE_STUDENT_ID is not set and failed to fetch student list: {e}. "
            f"Set it manually via {TOOL_SET_SECRET}."
        )

    if not edupage_students:
        return (
            "EDUPAGE_STUDENT_ID is not set and EduPage returned no students. "
            f"Set it manually via {TOOL_SET_SECRET}."
        )

    # Try auto-match by full_name
    if student_full_name:
        for s in edupage_students:
            if s.name.strip().lower() == student_full_name:
                return (
                    f"EDUPAGE_STUDENT_ID is not configured. "
                    f"Auto-match found: \"{s.name}\" (person_id={s.person_id}) "
                    f"matches student full_name in the database.\n\n"
                    f"To fix this, run: {TOOL_SET_SECRET}("
                    f"key=\"EDUPAGE_STUDENT_ID\", value=\"{s.person_id}\") "
                    f"and then retry {TOOL_RUN_SYNC}(provider_code=\"edupage\")."
                )

    # No auto-match — return full list for agent to ask the parent
    student_list = "\n".join(
        f"  - {s.name} (person_id={s.person_id})"
        for s in edupage_students
    )
    hint = (
        f" (student full_name: \"{student.full_name}\")"
        if student and student.full_name else ""
    )
    return (
        f"EDUPAGE_STUDENT_ID is not configured and strict auto-match failed"
        f"{hint}.\n\n"
        f"Students visible in EduPage:\n{student_list}\n\n"
        f"Your task:\n"
        f"1. Try to match the student yourself — names may differ in spelling, "
        f"diacritics, transliteration, or word order.\n"
        f"2. If you found a match — tell the parent who you matched and why, "
        f"then run: {TOOL_SET_SECRET}("
        f"key=\"EDUPAGE_STUDENT_ID\", value=\"<person_id>\") "
        f"and retry {TOOL_RUN_SYNC}(provider_code=\"edupage\").\n"
        f"3. If you are not confident — show the list to the parent "
        f"and ask them to pick their child."
    )


def _parse_grade_value(raw) -> int | None:
    """Parse EduPage grade value to int (1-5 scale).

    Handles: int, float, "1+", "2-", "3/4" patterns.
    Returns None if unparseable.
    """
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str):
        cleaned = raw.strip().rstrip("+-")
        try:
            return int(cleaned)
        except ValueError:
            match = re.match(r"^(\d)/(\d)$", cleaned)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
    return None
