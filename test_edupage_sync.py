#!/usr/bin/env python3
"""Test script for EduPage sync operations."""
import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def call_tool(tool_name: str, arguments: dict = None):
    """Call an MCP tool and return result."""
    params = StdioServerParameters(
        command='/home/geny/.cache/pypoetry/virtualenvs/learning-hub-mcp-Q3W67QO2-py3.12/bin/python',
        args=['-m', 'learning_hub.server']
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments or {})
            return result


async def test_sync_edupage():
    """Test EduPage sync operations."""
    print("=" * 60)
    print("EduPage Sync Tests")
    print("=" * 60)

    # Test 1: sync_edupage_grades - первый запуск
    print("\n[Test 1] sync_edupage_grades - первый запуск")
    print("-" * 60)
    try:
        result1 = await call_tool("sync_edupage_grades")
        print(f"Result: {result1.content}")

        # Parse result
        for item in result1.content:
            if hasattr(item, 'text'):
                data1 = json.loads(item.text)
                print(f"\nGrades fetched: {data1.get('grades_fetched')}")
                print(f"Grades created: {data1.get('grades_created')}")
                print(f"Grades skipped: {data1.get('grades_skipped')}")
                print(f"Subjects created: {data1.get('subjects_created')}")
                print(f"Errors: {data1.get('errors')}")

                # Validation
                if data1.get('grades_created', 0) > 0:
                    print("\n✓ Test 1 PASSED: grades_created > 0")
                    test1_grades = data1.get('grades_created')
                    test1_subjects = data1.get('subjects_created')
                else:
                    print("\n✗ Test 1 FAILED: grades_created = 0")
                    return
    except Exception as e:
        print(f"\n✗ Test 1 FAILED with error: {e}")
        return

    # Test 2: sync_edupage_grades - повторный запуск (дедупликация)
    print("\n[Test 2] sync_edupage_grades - повторный запуск (дедупликация)")
    print("-" * 60)
    try:
        result2 = await call_tool("sync_edupage_grades")

        for item in result2.content:
            if hasattr(item, 'text'):
                data2 = json.loads(item.text)
                print(f"\nGrades fetched: {data2.get('grades_fetched')}")
                print(f"Grades created: {data2.get('grades_created')}")
                print(f"Grades skipped: {data2.get('grades_skipped')}")
                print(f"Subjects created: {data2.get('subjects_created')}")
                print(f"Errors: {data2.get('errors')}")

                # Validation
                if data2.get('grades_created', -1) == 0:
                    print("\n✓ Test 2 PASSED: grades_created = 0 (all skipped)")
                else:
                    print(f"\n✗ Test 2 FAILED: grades_created = {data2.get('grades_created')} (expected 0)")
                    return
    except Exception as e:
        print(f"\n✗ Test 2 FAILED with error: {e}")
        return

    # Test 3: sync_edupage_homeworks - первый запуск
    print("\n[Test 3] sync_edupage_homeworks - первый запуск")
    print("-" * 60)
    try:
        result3 = await call_tool("sync_edupage_homeworks")

        for item in result3.content:
            if hasattr(item, 'text'):
                data3 = json.loads(item.text)
                print(f"\nHomeworks fetched: {data3.get('homeworks_fetched')}")
                print(f"Homeworks created: {data3.get('homeworks_created')}")
                print(f"Homeworks skipped: {data3.get('homeworks_skipped')}")
                print(f"Subjects created: {data3.get('subjects_created')}")
                print(f"Errors: {data3.get('errors')}")

                # Validation
                if data3.get('homeworks_created', 0) > 0:
                    print("\n✓ Test 3 PASSED: homeworks_created > 0")
                else:
                    print(f"\n✗ Test 3 FAILED: homeworks_created = {data3.get('homeworks_created')} (expected > 0)")
                    return
    except Exception as e:
        print(f"\n✗ Test 3 FAILED with error: {e}")
        return

    # Test 4: sync_edupage_homeworks - повторный запуск (дедупликация)
    print("\n[Test 4] sync_edupage_homeworks - повторный запуск (дедупликация)")
    print("-" * 60)
    try:
        result4 = await call_tool("sync_edupage_homeworks")

        for item in result4.content:
            if hasattr(item, 'text'):
                data4 = json.loads(item.text)
                print(f"\nHomeworks fetched: {data4.get('homeworks_fetched')}")
                print(f"Homeworks created: {data4.get('homeworks_created')}")
                print(f"Homeworks skipped: {data4.get('homeworks_skipped')}")
                print(f"Subjects created: {data4.get('subjects_created')}")
                print(f"Errors: {data4.get('errors')}")

                # Validation
                if data4.get('homeworks_created', -1) == 0:
                    print("\n✓ Test 4 PASSED: homeworks_created = 0 (all skipped)")
                else:
                    print(f"\n✗ Test 4 FAILED: homeworks_created = {data4.get('homeworks_created')} (expected 0)")
                    return
    except Exception as e:
        print(f"\n✗ Test 4 FAILED with error: {e}")
        return

    print("\n" + "=" * 60)
    print("All tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sync_edupage())
