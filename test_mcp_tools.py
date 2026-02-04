#!/usr/bin/env python3
"""Test script for Learning Hub MCP tools."""

import asyncio
from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import SchoolType, CloseReason
from learning_hub.repositories.subject import SubjectRepository
from learning_hub.repositories.subject_topic import SubjectTopicRepository

# Import all models to avoid SQLAlchemy relationship errors
from learning_hub.models import grade, subject, subject_topic, bonus_task, homework, week  # noqa: F401


async def test_subjects():
    """Test Subject tools."""
    print("\n" + "="*50)
    print("=== Subjects Tests ===")
    print("="*50)

    # Test 1: list_subjects - получить все предметы
    print("\n[Test 1] list_subjects - получить все предметы")
    async with AsyncSessionLocal() as session:
        repo = SubjectRepository(session)
        subjects = await repo.list()
        print(f"✓ Найдено предметов: {len(subjects)}")
        if subjects:
            print(f"  Примеры: {subjects[0].name} ({subjects[0].school.value})")
            if len(subjects) > 1:
                print(f"           {subjects[1].name} ({subjects[1].school.value})")

    # Test 2: create_subject - создать новый предмет
    print("\n[Test 2] create_subject - создать новый предмет")
    async with AsyncSessionLocal() as session:
        repo = SubjectRepository(session)
        new_subject = await repo.create(
            school=SchoolType.UA,
            name="Математика",
            name_ru="Математика",
            grade_level=7
        )
        print(f"✓ Создан предмет: id={new_subject.id}, name={new_subject.name}, school={new_subject.school.value}")
        created_subject_id = new_subject.id

    # Test 3: list_subjects с фильтром - фильтрация по школе
    print("\n[Test 3] list_subjects с фильтром school='UA'")
    async with AsyncSessionLocal() as session:
        repo = SubjectRepository(session)
        ua_subjects = await repo.list(school=SchoolType.UA)
        print(f"✓ Найдено UA предметов: {len(ua_subjects)}")
        for subj in ua_subjects:
            print(f"  - {subj.name} (id={subj.id})")

    # Test 4: update_subject - обновить предмет
    print("\n[Test 4] update_subject - обновить name_ru")
    async with AsyncSessionLocal() as session:
        repo = SubjectRepository(session)
        updated = await repo.update(
            subject_id=created_subject_id,
            name_ru="Математика (алгебра)"
        )
        if updated:
            print(f"✓ Обновлён предмет: name_ru={updated.name_ru}")
        else:
            print("✗ Предмет не найден")

    # Test 5: update_subject с невалидным ID - edge case
    print("\n[Test 5] update_subject с невалидным ID (99999)")
    async with AsyncSessionLocal() as session:
        repo = SubjectRepository(session)
        result = await repo.update(subject_id=99999, name_ru="Test")
        if result is None:
            print("✓ Вернул None для несуществующего ID")
        else:
            print("✗ Должен был вернуть None")

    return created_subject_id


async def test_topics(subject_id: int):
    """Test SubjectTopic tools."""
    print("\n" + "="*50)
    print("=== Topics Tests ===")
    print("="*50)

    # Test 6: create_topic - создать топик для предмета
    print(f"\n[Test 6] create_topic для subject_id={subject_id}")
    async with AsyncSessionLocal() as session:
        repo = SubjectTopicRepository(session)
        new_topic = await repo.create(
            subject_id=subject_id,
            description="Квадратные уравнения"
        )
        print(f"✓ Создан топик: id={new_topic.id}, description={new_topic.description}")
        created_topic_id = new_topic.id

    # Test 7: list_topics - получить топики
    print(f"\n[Test 7] list_topics с фильтром subject_id={subject_id}")
    async with AsyncSessionLocal() as session:
        repo = SubjectTopicRepository(session)
        topics = await repo.list(subject_id=subject_id)
        print(f"✓ Найдено топиков: {len(topics)}")
        for topic in topics:
            print(f"  - {topic.description} (id={topic.id}, open={topic.closed_at is None})")

    # Test 8: close_topic - закрыть топик
    print(f"\n[Test 8] close_topic с reason='RESOLVED'")
    async with AsyncSessionLocal() as session:
        repo = SubjectTopicRepository(session)
        closed = await repo.close(topic_id=created_topic_id, reason=CloseReason.RESOLVED)
        if closed and closed.closed_at:
            print(f"✓ Топик закрыт: closed_at={closed.closed_at}, reason={closed.close_reason.value}")
        else:
            print("✗ Топик не закрыт")

    # Test 9: list_topics с is_open=true - фильтр открытых
    print(f"\n[Test 9] list_topics с is_open=True (только открытые)")
    async with AsyncSessionLocal() as session:
        repo = SubjectTopicRepository(session)
        open_topics = await repo.list(subject_id=subject_id, is_open=True)
        has_closed = any(t.id == created_topic_id for t in open_topics)
        if not has_closed:
            print(f"✓ Закрытый топик отфильтрован (найдено открытых: {len(open_topics)})")
        else:
            print("✗ Закрытый топик не должен быть в списке")

    # Test 10: close_topic с невалидным ID - edge case
    print(f"\n[Test 10] close_topic с невалидным ID (99999)")
    async with AsyncSessionLocal() as session:
        repo = SubjectTopicRepository(session)
        result = await repo.close(topic_id=99999, reason=CloseReason.RESOLVED)
        if result is None:
            print("✓ Вернул None для несуществующего ID")
        else:
            print("✗ Должен был вернуть None")


async def main():
    """Run all tests."""
    print("Тестирование Learning Hub MCP сервера")
    print("База данных: data/learning_hub.db")

    subject_id = await test_subjects()
    await test_topics(subject_id)

    print("\n" + "="*50)
    print("Тестирование завершено!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
