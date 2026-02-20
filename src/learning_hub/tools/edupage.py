"""EduPage integration tools for MCP server."""

import re

from edupage_api import Edupage  # type: ignore[import-untyped]
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from learning_hub.config import settings
from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import GradeSource, GradeValue

# Import all models for SQLAlchemy relationship resolution
from learning_hub.models.school import School  # noqa: F401
from learning_hub.models.subject import Subject  # noqa: F401
from learning_hub.models.subject_topic import SubjectTopic  # noqa: F401
from learning_hub.models.grade import Grade  # noqa: F401
from learning_hub.models.bonus_task import BonusTask  # noqa: F401
from learning_hub.models.homework import Homework  # noqa: F401
from learning_hub.models.week import Week  # noqa: F401

from learning_hub.repositories.school import SchoolRepository
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.repositories.subject_topic import SubjectTopicRepository
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.repositories.topic_review import TopicReviewRepository
from learning_hub.tools.tool_names import (
    TOOL_GET_GRADE_ESCALATION_INSTRUCTIONS,
    TOOL_SYNC_EDUPAGE_GRADES,
    TOOL_SYNC_EDUPAGE_HOMEWORKS,
)


class GradesSyncResult(BaseModel):
    """Result of EduPage grades sync operation."""
    grades_fetched: int
    grades_created: int
    grades_skipped: int
    subjects_created: int
    topics_created: int
    reviews_created: int
    errors: list[str]


class HomeworksSyncResult(BaseModel):
    """Result of EduPage homeworks sync operation."""
    homeworks_fetched: int
    homeworks_created: int
    homeworks_skipped: int
    subjects_created: int
    errors: list[str]


def register_edupage_tools(mcp: FastMCP) -> None:
    """Register EduPage-related tools."""

    @mcp.tool(name=TOOL_SYNC_EDUPAGE_GRADES, description=f"""Sync grades from EduPage to local database.

    Fetches all grades from EduPage and saves them to the database.
    Creates subjects automatically if they don't exist.
    Skips grades that are already synced (by edupage_id).

    IMPORTANT: After this tool completes, always call
    `{TOOL_GET_GRADE_ESCALATION_INSTRUCTIONS}()` and follow the returned
    algorithm to escalate bad grades to responsible adults.

    Returns:
        Sync statistics: grades fetched/created/skipped, subjects created, errors
    """)
    async def sync_edupage_grades() -> GradesSyncResult:
        errors = []
        grades_created = 0
        grades_skipped = 0
        subjects_created = 0
        topics_created = 0
        reviews_created = 0

        # Check credentials
        if not settings.edupage_username or not settings.edupage_password:
            return GradesSyncResult(
                grades_fetched=0,
                grades_created=0,
                grades_skipped=0,
                subjects_created=0,
                topics_created=0,
                reviews_created=0,
                errors=["EduPage credentials not configured"],
            )

        # Connect to EduPage
        ep = Edupage()
        try:
            if settings.edupage_subdomain:
                ep.login(
                    settings.edupage_username,
                    settings.edupage_password,
                    settings.edupage_subdomain,
                )
            else:
                ep.login_auto(settings.edupage_username, settings.edupage_password)
        except Exception as e:
            return GradesSyncResult(
                grades_fetched=0,
                grades_created=0,
                grades_skipped=0,
                subjects_created=0,
                topics_created=0,
                reviews_created=0,
                errors=[f"EduPage login failed: {e}"],
            )

        # Fetch subjects for full names mapping
        try:
            edupage_subjects = ep.get_subjects()
            subject_names = {s.subject_id: s.name for s in edupage_subjects}
        except Exception as e:
            return GradesSyncResult(
                grades_fetched=0,
                grades_created=0,
                grades_skipped=0,
                subjects_created=0,
                topics_created=0,
                reviews_created=0,
                errors=[f"Failed to fetch subjects: {e}"],
            )

        # Fetch grades from EduPage
        try:
            edupage_grades = ep.get_grades()
        except Exception as e:
            return GradesSyncResult(
                grades_fetched=0,
                grades_created=0,
                grades_skipped=0,
                subjects_created=0,
                topics_created=0,
                reviews_created=0,
                errors=[f"Failed to fetch grades: {e}"],
            )

        # Look up school by code from config
        async with AsyncSessionLocal() as session:
            school_repo = SchoolRepository(session)
            school = await school_repo.get_by_code(settings.edupage_school)
            if school is None:
                return GradesSyncResult(
                    grades_fetched=len(edupage_grades),
                    grades_created=0,
                    grades_skipped=0,
                    subjects_created=0,
                    topics_created=0,
                    reviews_created=0,
                    errors=[
                        f"School with code '{settings.edupage_school}' not found. "
                        "Create it first with create_school tool."
                    ],
                )
            school_id = school.id

            subject_repo = SubjectRepository(session)
            topic_repo = SubjectTopicRepository(session)
            grade_repo = GradeRepository(session)
            review_repo = TopicReviewRepository(session)

            for eg in edupage_grades:
                # Check if already synced
                existing = await grade_repo.get_by_edupage_id(eg.event_id)
                if existing is not None:
                    grades_skipped += 1
                    continue

                # Parse grade value to int
                raw = eg.grade_n
                grade_int = None
                if isinstance(raw, (int, float)):
                    grade_int = int(raw)
                elif isinstance(raw, str):
                    # Strip +/- suffix (e.g. "1+" → "1", "2-" → "2")
                    cleaned = raw.strip().rstrip("+-")
                    # Try plain int first, then "3/4" pattern (take first number)
                    try:
                        grade_int = int(cleaned)
                    except ValueError:
                        match = re.match(r"^(\d)/(\d)$", cleaned)
                        if match:
                            try:
                                grade_int = int(match.group(1))
                            except ValueError:
                                pass

                if grade_int is None:
                    errors.append(f"Skipped non-numeric: {eg.subject_name} - {raw}")
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
                        edupage_id=eg.event_id,
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

        return GradesSyncResult(
            grades_fetched=len(edupage_grades),
            grades_created=grades_created,
            grades_skipped=grades_skipped,
            subjects_created=subjects_created,
            topics_created=topics_created,
            reviews_created=reviews_created,
            errors=errors,
        )

    @mcp.tool(name=TOOL_SYNC_EDUPAGE_HOMEWORKS, description="""Sync homeworks from EduPage to local database.

    Fetches homework assignments from EduPage notifications and saves them.
    Creates subjects automatically if they don't exist.
    Skips homeworks that are already synced (by edupage_id).

    Returns:
        Sync statistics: homeworks fetched/created/skipped, subjects created, errors
    """)
    async def sync_edupage_homeworks() -> HomeworksSyncResult:
        from datetime import datetime
        from edupage_api.timeline import EventType  # type: ignore[import-untyped]

        errors = []
        homeworks_created = 0
        homeworks_skipped = 0
        subjects_created = 0

        # Check credentials
        if not settings.edupage_username or not settings.edupage_password:
            return HomeworksSyncResult(
                homeworks_fetched=0,
                homeworks_created=0,
                homeworks_skipped=0,
                subjects_created=0,
                errors=["EduPage credentials not configured"],
            )

        # Connect to EduPage
        ep = Edupage()
        try:
            if settings.edupage_subdomain:
                ep.login(
                    settings.edupage_username,
                    settings.edupage_password,
                    settings.edupage_subdomain,
                )
            else:
                ep.login_auto(settings.edupage_username, settings.edupage_password)
        except Exception as e:
            return HomeworksSyncResult(
                homeworks_fetched=0,
                homeworks_created=0,
                homeworks_skipped=0,
                subjects_created=0,
                errors=[f"EduPage login failed: {e}"],
            )

        # Fetch subjects for full names mapping
        try:
            edupage_subjects = ep.get_subjects()
            subject_names = {str(s.subject_id): s.name for s in edupage_subjects}
        except Exception as e:
            return HomeworksSyncResult(
                homeworks_fetched=0,
                homeworks_created=0,
                homeworks_skipped=0,
                subjects_created=0,
                errors=[f"Failed to fetch subjects: {e}"],
            )

        # Fetch notifications and filter homework events
        try:
            notifications = ep.get_notifications()
            homework_events = [
                n for n in notifications
                if n.event_type == EventType.HOMEWORK
            ]
        except Exception as e:
            return HomeworksSyncResult(
                homeworks_fetched=0,
                homeworks_created=0,
                homeworks_skipped=0,
                subjects_created=0,
                errors=[f"Failed to fetch notifications: {e}"],
            )

        # Look up school by code from config
        async with AsyncSessionLocal() as session:
            school_repo = SchoolRepository(session)
            school = await school_repo.get_by_code(settings.edupage_school)
            if school is None:
                return HomeworksSyncResult(
                    homeworks_fetched=len(homework_events),
                    homeworks_created=0,
                    homeworks_skipped=0,
                    subjects_created=0,
                    errors=[
                        f"School with code '{settings.edupage_school}' not found. "
                        "Create it first with create_school tool."
                    ],
                )
            school_id = school.id

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
                existing = await homework_repo.get_by_edupage_id(edupage_id)
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
                        pass

                # Check if deadline already passed - mark as done
                from learning_hub.models.enums import HomeworkStatus
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
                        edupage_id=edupage_id,
                        status=status,
                    )
                    homeworks_created += 1
                except Exception as e:
                    errors.append(f"Failed to create homework: {e}")

        return HomeworksSyncResult(
            homeworks_fetched=len(homework_events),
            homeworks_created=homeworks_created,
            homeworks_skipped=homeworks_skipped,
            subjects_created=subjects_created,
            errors=errors,
        )
