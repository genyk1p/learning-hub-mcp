"""Tests for get_priority_topic_for_review wave 1 + wave 2 and list_with_topics_since."""

from datetime import datetime, timedelta

import pytest

from learning_hub.models.enums import (
    GradeValue,
    TopicReviewStatus,
)
from learning_hub.models.grade import Grade
from learning_hub.models.school import School
from learning_hub.models.subject import Subject
from learning_hub.models.subject_topic import SubjectTopic
from learning_hub.models.topic_review import TopicReview
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.topic_review import TopicReviewRepository


pytestmark = pytest.mark.asyncio


# ---- helpers ----


async def _make_school(session, code="CZ", name="Czech School") -> School:
    school = School(code=code, name=name, is_active=True)
    session.add(school)
    await session.flush()
    return school


async def _make_subject(session, school_id: int, name: str) -> Subject:
    subject = Subject(school_id=school_id, name=name)
    session.add(subject)
    await session.flush()
    return subject


async def _make_topic(session, subject_id: int, description: str) -> SubjectTopic:
    topic = SubjectTopic(subject_id=subject_id, description=description)
    session.add(topic)
    await session.flush()
    return topic


async def _make_grade(
    session,
    subject_id: int,
    grade_value: GradeValue,
    date: datetime | None = None,
    subject_topic_id: int | None = None,
) -> Grade:
    grade = Grade(
        subject_id=subject_id,
        grade_value=grade_value,
        date=date or datetime.now(),
        subject_topic_id=subject_topic_id,
    )
    session.add(grade)
    await session.flush()
    return grade


async def _make_review(
    session,
    subject_id: int,
    subject_topic_id: int,
    grade_id: int,
    repeat_count: int = 0,
) -> TopicReview:
    review = TopicReview(
        subject_id=subject_id,
        subject_topic_id=subject_topic_id,
        grade_id=grade_id,
        status=TopicReviewStatus.PENDING,
        repeat_count=repeat_count,
    )
    session.add(review)
    await session.flush()
    return review


# ---- list_with_topics_since tests ----


async def test_list_with_topics_returns_grades_with_topic(session):
    """Only returns grades that have a linked topic."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Math")
    topic = await _make_topic(session, subj.id, "Fractions")

    # Grade with topic
    await _make_grade(session, subj.id, GradeValue.GOOD, subject_topic_id=topic.id)
    # Grade without topic
    await _make_grade(session, subj.id, GradeValue.POOR)
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 1
    assert grades[0].subject_topic_id == topic.id


async def test_list_with_topics_excludes_excellent(session):
    """Grades with value 1 (excellent) are excluded."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Math")
    topic = await _make_topic(session, subj.id, "Fractions")

    await _make_grade(session, subj.id, GradeValue.EXCELLENT, subject_topic_id=topic.id)
    await _make_grade(session, subj.id, GradeValue.SATISFACTORY, subject_topic_id=topic.id)
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 1
    assert grades[0].grade_value == GradeValue.SATISFACTORY


async def test_list_with_topics_respects_since(session):
    """Only returns grades after the since date."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Math")
    topic = await _make_topic(session, subj.id, "Fractions")

    # Recent grade
    await _make_grade(session, subj.id, GradeValue.GOOD, subject_topic_id=topic.id)
    # Old grade (60 days ago)
    await _make_grade(
        session, subj.id, GradeValue.POOR,
        date=datetime.now() - timedelta(days=60),
        subject_topic_id=topic.id,
    )
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 1
    assert grades[0].grade_value == GradeValue.GOOD


async def test_list_with_topics_empty_when_all_excellent(session):
    """Returns empty if all grades with topics are excellent."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Math")
    topic = await _make_topic(session, subj.id, "Fractions")

    await _make_grade(session, subj.id, GradeValue.EXCELLENT, subject_topic_id=topic.id)
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 0


async def test_list_with_topics_eager_loads_relations(session):
    """Subject and subject_topic are eagerly loaded."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Physics")
    topic = await _make_topic(session, subj.id, "Gravity")

    await _make_grade(session, subj.id, GradeValue.POOR, subject_topic_id=topic.id)
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 1
    assert grades[0].subject.name == "Physics"
    assert grades[0].subject_topic.description == "Gravity"


# ---- wave 1 tests (priority candidates) ----


async def test_wave1_returns_reinforcement_source(session):
    """When pending TopicReviews exist, returns review_source=reinforcement."""
    school = await _make_school(session)
    subj = await _make_subject(session, school.id, "Math")
    topic = await _make_topic(session, subj.id, "Fractions")
    grade = await _make_grade(session, subj.id, GradeValue.POOR, subject_topic_id=topic.id)
    await _make_review(session, subj.id, topic.id, grade.id)
    await session.commit()

    repo = TopicReviewRepository(session)
    candidates = await repo.get_top_priority_candidates(limit=4)

    assert len(candidates) == 1
    review = candidates[0]
    assert review.status == TopicReviewStatus.PENDING
    assert review.grade.grade_value == GradeValue.POOR


# ---- wave 2 tests (fallback from grades) ----


async def test_wave2_favorite_subject_filtering(session):
    """Wave 2 grades can be filtered by favorite subject IDs."""
    school = await _make_school(session)
    fav_subj = await _make_subject(session, school.id, "Favorite Subject")
    fav_subj.is_favorite = True
    other_subj = await _make_subject(session, school.id, "Other Subject")
    fav_topic = await _make_topic(session, fav_subj.id, "Fav topic")
    other_topic = await _make_topic(session, other_subj.id, "Other topic")

    await _make_grade(session, fav_subj.id, GradeValue.GOOD, subject_topic_id=fav_topic.id)
    await _make_grade(session, other_subj.id, GradeValue.POOR, subject_topic_id=other_topic.id)
    await session.commit()

    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    # Both grades returned
    assert len(grades) == 2

    # Filtering by favorite IDs gives only the favorite subject's grades
    favorite_ids = {fav_subj.id}
    favorite_grades = [g for g in grades if g.subject_id in favorite_ids]
    assert len(favorite_grades) == 1
    assert favorite_grades[0].subject_id == fav_subj.id


async def test_wave2_returns_none_when_no_grades(session):
    """Wave 2 returns empty list when no grades exist."""
    repo = GradeRepository(session)
    since = datetime.now() - timedelta(days=30)
    grades = await repo.list_with_topics_since(since)

    assert len(grades) == 0
