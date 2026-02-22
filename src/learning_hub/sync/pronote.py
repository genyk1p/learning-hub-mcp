"""PRONOTE sync implementation.

Syncs grades and homeworks from PRONOTE via pronotepy into the local database.
Called by the run_sync dispatcher — not exposed as a standalone MCP tool.
"""

import datetime

import pronotepy  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from learning_hub.models.enums import (
    GradeSource,
    GradeValue,
    HomeworkStatus,
    SyncProviderType,
)
from learning_hub.models.sync_provider import SyncProvider
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.repositories.secret import SecretRepository
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.repositories.subject_topic import SubjectTopicRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.sync.result import ProviderSyncResult


async def run_pronote_sync(
    session: AsyncSession,
    provider: SyncProvider,
) -> ProviderSyncResult:
    """Run full PRONOTE sync (grades + homeworks).

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
    pronote_url = await secret_repo.get_value("PRONOTE_URL")
    username = await secret_repo.get_value("PRONOTE_USERNAME")
    password = await secret_repo.get_value("PRONOTE_PASSWORD")

    if not pronote_url or not username or not password:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[
                "PRONOTE credentials not configured. "
                "Set PRONOTE_URL, PRONOTE_USERNAME, and PRONOTE_PASSWORD "
                "via set_secret."
            ],
        )

    # Connect to PRONOTE
    try:
        client = pronotepy.Client(pronote_url, username=username, password=password)
    except Exception as e:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=[f"PRONOTE connection failed: {type(e).__name__}: {e}"],
        )

    if not client.logged_in:
        return ProviderSyncResult(
            provider_code=provider.code,
            provider_name=provider.name,
            school_name=school_name,
            errors=["PRONOTE login failed: client not logged in"],
        )

    # --- Sync grades ---
    grades_result = await _sync_grades(session, client, school_id, errors)

    # --- Sync homeworks ---
    homeworks_result = await _sync_homeworks(session, client, school_id, errors)

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
    client: pronotepy.Client,
    school_id: int,
    errors: list[str],
) -> dict:
    """Sync grades from all PRONOTE periods. Returns stats dict."""
    grades_created = 0
    grades_skipped = 0
    grades_fetched = 0
    subjects_created = 0
    topics_created = 0
    reviews_created = 0

    subject_repo = SubjectRepository(session)
    topic_repo = SubjectTopicRepository(session)
    grade_repo = GradeRepository(session)
    review_repo = TopicReviewRepository(session)

    for period in client.periods:
        try:
            pronote_grades = period.grades
        except Exception as e:
            errors.append(f"Failed to fetch grades for {period.name}: {e}")
            continue

        grades_fetched += len(pronote_grades)

        for pg in pronote_grades:
            # Check if already synced
            existing = await grade_repo.get_by_external_id(
                pg.id, SyncProviderType.PRONOTE
            )
            if existing is not None:
                grades_skipped += 1
                continue

            # Parse grade value
            grade_float = _parse_pronote_float(pg.grade)
            if grade_float is None:
                errors.append(
                    f"Skipped non-numeric grade: {pg.subject.name} - '{pg.grade}'"
                )
                grades_skipped += 1
                continue

            out_of_float = _parse_pronote_float(pg.out_of)
            if out_of_float is None or out_of_float <= 0:
                errors.append(
                    f"Invalid out_of '{pg.out_of}' for "
                    f"{pg.subject.name} on {pg.date}"
                )
                grades_skipped += 1
                continue

            # Map to 1-5 scale
            grade_int = _map_grade_to_scale(grade_float, out_of_float)
            if grade_int is None:
                errors.append(
                    f"Grade mapping failed for {pg.subject.name}: "
                    f"{grade_float}/{out_of_float}"
                )
                grades_skipped += 1
                continue

            grade_value = GradeValue(grade_int)

            # Parse subject name (split "MATHÉMATIQUES > Écrit")
            subject_name, topic_name = _parse_subject_name(pg.subject.name)

            # Find or create subject
            subject, created = await subject_repo.get_or_create(
                school_id=school_id,
                name=subject_name,
            )
            if created:
                subjects_created += 1

            # Find or create topic if present
            subject_topic_id = None
            if topic_name:
                topic, topic_created = await topic_repo.get_or_create(
                    subject_id=subject.id,
                    description=topic_name,
                )
                subject_topic_id = topic.id
                if topic_created:
                    topics_created += 1

            # Also use comment as topic if no topic from subject name
            if not topic_name and pg.comment and pg.comment.strip():
                comment_text = pg.comment.strip()
                topic, topic_created = await topic_repo.get_or_create(
                    subject_id=subject.id,
                    description=comment_text,
                )
                subject_topic_id = topic.id
                if topic_created:
                    topics_created += 1

            # Create grade
            try:
                grade = await grade_repo.create(
                    subject_id=subject.id,
                    grade_value=grade_value,
                    date=pg.date if isinstance(pg.date, datetime.datetime)
                    else datetime.datetime.combine(
                        pg.date, datetime.time()
                    ),
                    subject_topic_id=subject_topic_id,
                    external_id=pg.id,
                    external_source=SyncProviderType.PRONOTE,
                    source=GradeSource.AUTO,
                    original_value=f"{pg.grade}/{pg.out_of}",
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
                errors.append(
                    f"Failed to create grade for {pg.subject.name}: {e}"
                )

    return {
        "grades_fetched": grades_fetched,
        "grades_created": grades_created,
        "grades_skipped": grades_skipped,
        "subjects_created": subjects_created,
        "topics_created": topics_created,
        "reviews_created": reviews_created,
    }


async def _sync_homeworks(
    session: AsyncSession,
    client: pronotepy.Client,
    school_id: int,
    errors: list[str],
) -> dict:
    """Sync homeworks from PRONOTE. Returns stats dict."""
    homeworks_created = 0
    homeworks_skipped = 0

    subjects_created = 0

    # Fetch homework from the start of the school year
    try:
        start_date = client.start_day.date() if isinstance(
            client.start_day, datetime.datetime
        ) else client.start_day
        pronote_homeworks = client.homework(start_date)
    except Exception as e:
        errors.append(f"Failed to fetch homeworks: {e}")
        return {
            "homeworks_fetched": 0,
            "homeworks_created": 0,
            "homeworks_skipped": 0,
            "subjects_created": 0,
        }

    subject_repo = SubjectRepository(session)
    homework_repo = HomeworkRepository(session)

    for hw in pronote_homeworks:
        # Check if already synced
        existing = await homework_repo.get_by_external_id(
            hw.id, SyncProviderType.PRONOTE
        )
        if existing is not None:
            homeworks_skipped += 1
            continue

        # Parse subject name (take only the subject part, not subcategory)
        subject_name, _ = _parse_subject_name(hw.subject.name)

        subject, created = await subject_repo.get_or_create(
            school_id=school_id,
            name=subject_name,
        )
        if created:
            subjects_created += 1

        # Deadline
        deadline_at = None
        if hw.date:
            deadline_at = (
                hw.date if isinstance(hw.date, datetime.datetime)
                else datetime.datetime.combine(hw.date, datetime.time())
            )

        # Status: if deadline passed, mark as DONE
        status = HomeworkStatus.PENDING
        if deadline_at and deadline_at < datetime.datetime.now():
            status = HomeworkStatus.DONE

        # Extract link attachments (type=0 only, skip files)
        attachment_url = None
        try:
            for f in hw.files:
                if f.type == 0:
                    attachment_url = f.url
                    break
        except Exception as e:
            errors.append(
                f"Failed to extract attachment for {hw.subject.name}: "
                f"{type(e).__name__}: {e}"
            )

        try:
            await homework_repo.create(
                subject_id=subject.id,
                description=hw.description or "No description",
                deadline_at=deadline_at,
                external_id=hw.id,
                external_source=SyncProviderType.PRONOTE,
                status=status,
                attachment_url=attachment_url,
            )
            homeworks_created += 1
        except Exception as e:
            errors.append(
                f"Failed to create homework for {hw.subject.name}: {e}"
            )

    return {
        "homeworks_fetched": len(pronote_homeworks),
        "homeworks_created": homeworks_created,
        "homeworks_skipped": homeworks_skipped,
        "subjects_created": subjects_created,
    }


def _parse_pronote_float(value) -> float | None:
    """Parse PRONOTE numeric value to float.

    Handles French comma decimals ('17,5' -> 17.5),
    numeric types (int/float passthrough), and
    skips special values ('Absent', 'NonRendu', etc.).
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _map_grade_to_scale(value: float, out_of: float) -> int | None:
    """Map PRONOTE grade to 1-5 scale.

    Normalizes to /20, then applies thresholds:
      16-20   -> 1 (Excellent)
      14-15.9 -> 2 (Good)
      10-13.9 -> 3 (Satisfactory)
      6-9.9   -> 4 (Poor)
      0-5.9   -> 5 (Fail)
    """
    if out_of <= 0:
        return None
    normalized = (value / out_of) * 20
    if normalized >= 16:
        return 1
    if normalized >= 14:
        return 2
    if normalized >= 10:
        return 3
    if normalized >= 6:
        return 4
    return 5


def _parse_subject_name(raw_name: str) -> tuple[str, str | None]:
    """Split PRONOTE subject name into subject and optional topic.

    'MATHÉMATIQUES > Écrit' -> ('MATHÉMATIQUES', 'Écrit')
    'HISTOIRE-GÉOGRAPHIE'   -> ('HISTOIRE-GÉOGRAPHIE', None)
    """
    if " > " in raw_name:
        subject, topic = raw_name.split(" > ", 1)
        return subject.strip(), topic.strip()
    return raw_name.strip(), None
