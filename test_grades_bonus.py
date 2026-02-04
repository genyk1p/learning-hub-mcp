#!/usr/bin/env python3
"""Test script for Grades and BonusTasks MCP tools."""

import asyncio
from datetime import datetime
from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import GradeValue, SchoolType, BonusTaskStatus
from learning_hub.repositories.grade import GradeRepository
from learning_hub.repositories.bonus_task import BonusTaskRepository
from learning_hub.repositories.subject_topic import SubjectTopicRepository

# Import all models to avoid SQLAlchemy relationship errors
from learning_hub.models import grade, subject, subject_topic, bonus_task, homework, week  # noqa: F401


async def test_grades():
    """Test Grade tools."""
    print("\n" + "="*50)
    print("=== Grades Tests ===")
    print("="*50)

    # Test 1: list_grades - получить все оценки
    print("\n[Test 1] list_grades - получить все оценки")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        grades = await repo.list()
        print(f"✓ Найдено оценок: {len(grades)}")
        if grades:
            print(f"  Первая оценка: grade={grades[0].grade_value.value}, subject_id={grades[0].subject_id}")
            if len(grades) >= 8:
                print(f"  Должно быть 8 оценок от EduPage: {'✓' if len(grades) >= 8 else '✗'}")

    # Test 2: list_grades с фильтром school="CZ"
    print("\n[Test 2] list_grades с фильтром school='CZ'")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        cz_grades = await repo.list(school=SchoolType.CZ)
        print(f"✓ Найдено CZ оценок: {len(cz_grades)}")
        for g in cz_grades[:3]:
            print(f"  - grade={g.grade_value.value}, subject_id={g.subject_id}, date={g.date}")

    # Test 2b: list_grades с фильтром date_from/date_to
    print("\n[Test 2b] list_grades с фильтром date_from/date_to")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        date_from = datetime(2026, 1, 1)
        date_to = datetime(2026, 12, 31)
        filtered_grades = await repo.list(date_from=date_from, date_to=date_to)
        print(f"✓ Найдено оценок за 2026 год: {len(filtered_grades)}")

    # Test 2c: list_grades с фильтром rewarded=false
    print("\n[Test 2c] list_grades с фильтром rewarded=False")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        unrewarded = await repo.list(rewarded=False)
        print(f"✓ Найдено ненаграждённых оценок: {len(unrewarded)}")

    # Test 3: add_grade - добавить оценку вручную
    print("\n[Test 3] add_grade - добавить оценку для subject_id=8 (Математика UA)")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        new_grade = await repo.create(
            subject_id=8,
            grade_value=GradeValue.EXCELLENT,  # 1 = отлично
            date=datetime(2026, 2, 4),
            topic_text="Контрольная по квадратным уравнениям"
        )
        print(f"✓ Создана оценка: id={new_grade.id}, grade={new_grade.grade_value.value}, subject_id={new_grade.subject_id}")
        print(f"  topic_text={new_grade.topic_text}")
        created_grade_id = new_grade.id

    # Test 4: update_grade - обновить оценку
    print("\n[Test 4] update_grade - пометить оценку как rewarded=True")
    async with AsyncSessionLocal() as session:
        repo = GradeRepository(session)
        updated = await repo.update(
            grade_id=created_grade_id,
            rewarded=True,
            topic_received_at=datetime.now()
        )
        if updated:
            print(f"✓ Оценка обновлена: rewarded={updated.rewarded}, topic_received_at={updated.topic_received_at}")
        else:
            print("✗ Оценка не найдена")

    # Test 5: add_grade с невалидным grade_value - edge case
    print("\n[Test 5] add_grade с невалидным grade_value=6 (edge case)")
    try:
        async with AsyncSessionLocal() as session:
            repo = GradeRepository(session)
            invalid_grade = await repo.create(
                subject_id=8,
                grade_value=6,  # Вне диапазона 1-5
                date=datetime(2026, 2, 4)
            )
        print(f"✗ Должна была быть ошибка, но создана оценка: {invalid_grade.id}")
    except (ValueError, Exception) as e:
        print(f"✓ Получена ожидаемая ошибка: {type(e).__name__}")


async def test_bonus_tasks():
    """Test BonusTask tools."""
    print("\n" + "="*50)
    print("=== BonusTasks Tests ===")
    print("="*50)

    # Сначала создаём открытый топик для тестов
    print("\n[Setup] create_topic для subject_id=8 (Математика UA)")
    async with AsyncSessionLocal() as session:
        topic_repo = SubjectTopicRepository(session)
        new_topic = await topic_repo.create(
            subject_id=8,
            description="Линейные уравнения"
        )
        print(f"✓ Создан топик: id={new_topic.id}, description={new_topic.description}")
        test_topic_id = new_topic.id

    # Test 6: create_bonus_task - создать бонусную задачу
    print(f"\n[Test 6] create_bonus_task для topic_id={test_topic_id}")
    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        task = await repo.create(
            subject_topic_id=test_topic_id,
            task_description="Решить 10 дополнительных уравнений",
            minutes_promised=30
        )
        print(f"✓ Создана задача: id={task.id}, description={task.task_description}")
        print(f"  minutes_promised={task.minutes_promised}, status={task.status.value}")
        task_id_1 = task.id

    # Test 7: list_bonus_tasks - получить задачи
    print("\n[Test 7] list_bonus_tasks с фильтром status='PROMISED'")
    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        promised_tasks = await repo.list(status=BonusTaskStatus.PROMISED)
        print(f"✓ Найдено PROMISED задач: {len(promised_tasks)}")
        for t in promised_tasks:
            print(f"  - id={t.id}, task={t.task_description[:40]}..., minutes={t.minutes_promised}")

    # Test 8: complete_bonus_task - завершить задачу
    print(f"\n[Test 8] complete_bonus_task для task_id={task_id_1}")
    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        completed = await repo.complete(
            task_id=task_id_1,
            quality_notes="Отлично выполнено"
        )
        if completed:
            print(f"✓ Задача завершена: status={completed.status.value}")
            print(f"  completed_at={completed.completed_at}, quality_notes={completed.quality_notes}")
        else:
            print("✗ Задача не найдена")

    # Test 9: create_bonus_task + cancel_bonus_task - отмена
    print(f"\n[Test 9] create_bonus_task + cancel_bonus_task")
    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        task2 = await repo.create(
            subject_topic_id=test_topic_id,
            task_description="Дополнительные задачи на повторение",
            minutes_promised=20
        )
        print(f"  Создана задача: id={task2.id}")
        task_id_2 = task2.id

    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        cancelled = await repo.cancel(task_id=task_id_2)
        if cancelled:
            print(f"✓ Задача отменена: status={cancelled.status.value}")
            if cancelled.status == BonusTaskStatus.CANCELLED:
                print("  Статус CANCELLED - верно!")
        else:
            print("✗ Задача не найдена")

    # Test 10: complete_bonus_task с невалидным ID - edge case
    print("\n[Test 10] complete_bonus_task с невалидным task_id=99999 (edge case)")
    async with AsyncSessionLocal() as session:
        repo = BonusTaskRepository(session)
        result = await repo.complete(task_id=99999, quality_notes="Test")
        if result is None:
            print("✓ Вернул None для несуществующего ID")
        else:
            print("✗ Должен был вернуть None")


async def main():
    """Run all tests."""
    print("Тестирование Grades и BonusTasks")
    print("База данных: data/learning_hub.db")

    await test_grades()
    await test_bonus_tasks()

    print("\n" + "="*50)
    print("Тестирование завершено!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
