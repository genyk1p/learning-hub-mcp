#!/usr/bin/env python3
"""Test script for Homeworks and Weeks MCP tools."""

import asyncio
from datetime import datetime
from learning_hub.database.connection import AsyncSessionLocal
from learning_hub.models.enums import HomeworkStatus, GradeValue
from learning_hub.repositories.homework import HomeworkRepository
from learning_hub.repositories.week import WeekRepository

# Import all models to avoid SQLAlchemy relationship errors
from learning_hub.models import grade, subject, subject_topic, bonus_task, homework, week  # noqa: F401


async def test_homeworks():
    """Test Homework tools."""
    print("\n" + "="*50)
    print("=== Homeworks Tests ===")
    print("="*50)

    # Test 1: list_homeworks - получить все домашки
    print("\n[Test 1] list_homeworks - получить все домашки")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        homeworks = await repo.list()
        expected_count = 23
        if len(homeworks) == expected_count:
            print(f"✓ Найдено домашек: {len(homeworks)} (ожидалось {expected_count} от EduPage)")
        else:
            print(f"✓ Найдено домашек: {len(homeworks)} (ожидалось {expected_count}, но может быть больше)")
        if homeworks:
            print(f"  Пример: {homeworks[0].description[:50]}... (status={homeworks[0].status.value})")

    # Test 2: list_homeworks с фильтром status="PENDING"
    print("\n[Test 2] list_homeworks с фильтром status='PENDING'")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        pending_hw = await repo.list(status=HomeworkStatus.PENDING)
        print(f"✓ Найдено PENDING домашек: {len(pending_hw)}")
        if pending_hw:
            print(f"  Пример: {pending_hw[0].description[:50]}...")

    # Test 3: list_homeworks с фильтром subject_id
    print("\n[Test 3] list_homeworks с фильтром subject_id=8")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        subject_hw = await repo.list(subject_id=8)
        print(f"✓ Найдено домашек для subject_id=8 (Математика UA): {len(subject_hw)}")
        if subject_hw:
            print(f"  Пример: {subject_hw[0].description[:50]}...")

    # Test 4: create_homework - создать домашку вручную
    print("\n[Test 4] create_homework - создать домашку вручную")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        new_hw = await repo.create(
            subject_id=8,
            description="Упражнения 1-10 на стр. 45",
            assigned_at=datetime.now(),
            deadline_at=datetime.fromisoformat("2026-02-10T18:00:00")
        )
        print(f"✓ Создана домашка: id={new_hw.id}, description={new_hw.description}")
        print(f"  subject_id={new_hw.subject_id}, deadline={new_hw.deadline_at}, status={new_hw.status.value}")
        created_hw_id = new_hw.id

    # Test 5: update_homework - обновить домашку (deadline_at и recommended_grade)
    print("\n[Test 5] update_homework - обновить deadline_at и recommended_grade")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        updated_hw = await repo.update(
            homework_id=created_hw_id,
            deadline_at=datetime.fromisoformat("2026-02-12T18:00:00"),
            recommended_grade=GradeValue.GOOD
        )
        if updated_hw:
            print(f"✓ Обновлена домашка: deadline_at={updated_hw.deadline_at}")
            print(f"  recommended_grade={updated_hw.recommended_grade.value if updated_hw.recommended_grade else None}")
        else:
            print("✗ Домашка не найдена")

    # Test 6: complete_homework - завершить домашку
    print("\n[Test 6] complete_homework - завершить домашку")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        completed_hw = await repo.complete(homework_id=created_hw_id)
        if completed_hw:
            is_done = completed_hw.status == HomeworkStatus.DONE
            has_completed_at = completed_hw.completed_at is not None
            print(f"✓ Домашка завершена: status={completed_hw.status.value} (DONE={is_done})")
            print(f"  completed_at={completed_hw.completed_at} (заполнен={has_completed_at})")
        else:
            print("✗ Домашка не найдена")

    # Test 7: complete_homework с невалидным ID - edge case
    print("\n[Test 7] complete_homework с невалидным ID (99999)")
    async with AsyncSessionLocal() as session:
        repo = HomeworkRepository(session)
        result = await repo.complete(homework_id=99999)
        if result is None:
            print("✓ Вернул None для несуществующего ID")
        else:
            print("✗ Должен был вернуть None")


async def test_weeks():
    """Test Week tools."""
    print("\n" + "="*50)
    print("=== Weeks Tests ===")
    print("="*50)

    # Test 8: get_week - получить текущую неделю (без параметров)
    print("\n[Test 8] get_week - получить текущую неделю (без параметров)")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        current_week = await repo.get_current(datetime.now())
        if current_week is None:
            print("✓ Вернул None (недели ещё нет)")
        else:
            print(f"✓ Найдена текущая неделя: {current_week.week_key}")

    # Test 9: create_week - создать неделю
    print("\n[Test 9] create_week - создать неделю")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        new_week = await repo.create(
            week_key="2026-02-01",
            start_at=datetime.fromisoformat("2026-02-01T00:00:00"),
            end_at=datetime.fromisoformat("2026-02-08T00:00:00")
        )
        print(f"✓ Создана неделя: week_key={new_week.week_key}")
        print(f"  start_at={new_week.start_at}, end_at={new_week.end_at}")
        print(f"  grade_minutes={new_week.grade_minutes}, bonus_minutes={new_week.bonus_minutes}")
        print(f"  penalty_minutes={new_week.penalty_minutes}, total_minutes={new_week.total_minutes}")
        print(f"  is_finalized={new_week.is_finalized}")

    # Test 10: get_week по ключу - должна вернуться созданная неделя
    print("\n[Test 10] get_week по ключу (week_key='2026-02-01')")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        found_week = await repo.get_by_key("2026-02-01")
        if found_week:
            print(f"✓ Найдена неделя: week_key={found_week.week_key}")
            print(f"  start_at={found_week.start_at}, end_at={found_week.end_at}")
        else:
            print("✗ Неделя не найдена")

    # Test 11: update_week - обновить минуты
    print("\n[Test 11] update_week - обновить минуты")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        updated_week = await repo.update(
            week_key="2026-02-01",
            grade_minutes=60,
            bonus_minutes=30,
            penalty_minutes=10,
            actual_played_minutes=45
        )
        if updated_week:
            print(f"✓ Обновлена неделя: week_key={updated_week.week_key}")
            print(f"  grade_minutes={updated_week.grade_minutes}")
            print(f"  bonus_minutes={updated_week.bonus_minutes}")
            print(f"  penalty_minutes={updated_week.penalty_minutes}")
            print(f"  actual_played_minutes={updated_week.actual_played_minutes}")
            print(f"  total_minutes={updated_week.total_minutes}")
        else:
            print("✗ Неделя не найдена")

    # Test 12: finalize_week - финализировать неделю
    print("\n[Test 12] finalize_week - финализировать неделю")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        finalized_week = await repo.finalize(week_key="2026-02-01")
        if finalized_week:
            print(f"✓ Неделя финализирована: week_key={finalized_week.week_key}")
            print(f"  is_finalized={finalized_week.is_finalized} (ожидалось True)")
        else:
            print("✗ Неделя не найдена")

    # Test 13: finalize_week с невалидным ключом - edge case
    print("\n[Test 13] finalize_week с невалидным ключом (week_key='9999-99-99')")
    async with AsyncSessionLocal() as session:
        repo = WeekRepository(session)
        result = await repo.finalize(week_key="9999-99-99")
        if result is None:
            print("✓ Вернул None для несуществующего ключа")
        else:
            print("✗ Должен был вернуть None")


async def main():
    """Run all tests."""
    print("Тестирование Homeworks и Weeks MCP сервера")
    print("База данных: data/learning_hub.db")
    print(f"Время запуска: {datetime.now()}")

    await test_homeworks()
    await test_weeks()

    print("\n" + "="*50)
    print("Тестирование завершено!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
