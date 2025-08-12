import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.tools.task_tools import (
    initialize_tools,
    create_reminder_task,
    query_reminder_tasks,
    complete_reminder_task,
    delete_reminder_task,
    update_reminder_task,
    recommend_next_task,
    analyze_task_workload
)
from src.state.schemas import Task, TaskPriority, TaskStatus

# Pytest's 'asyncio' marker is needed for async tests
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_managers():
    """Fixture to create mock tool and LLM managers for testing."""
    mock_tool_manager = MagicMock()
    # We need to mock the reminders_tool attribute specifically
    mock_tool_manager.reminders_tool = MagicMock()
    
    mock_llm_manager = MagicMock()
    mock_llm_manager.client = AsyncMock()
    
    # Initialize the tools module with our mock managers
    initialize_tools(mock_tool_manager, mock_llm_manager)
    return mock_tool_manager, mock_llm_manager

# --- Test Cases ---

async def test_create_reminder_task_success(mock_managers):
    """Verify that create_reminder_task successfully creates a task."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.create_reminder = AsyncMock(return_value="task_123")

    result = await create_reminder_task(title="Test Task", priority=TaskPriority.HIGH)
    
    assert "✅ Task 'Test Task' created successfully with ID: task_123." in result
    mock_tool_manager.reminders_tool.create_reminder.assert_called_once()
    # Check that the first argument of the call is a Task object with correct attributes
    call_args = mock_tool_manager.reminders_tool.create_reminder.call_args[0][0]
    assert isinstance(call_args, Task)
    assert call_args.title == "Test Task"
    assert call_args.priority == TaskPriority.HIGH

async def test_create_reminder_task_failure(mock_managers):
    """Verify that create_reminder_task handles exceptions gracefully."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.create_reminder = AsyncMock(side_effect=Exception("MCP Error"))

    result = await create_reminder_task(title="Test Fail")
    
    assert "❌ An error occurred while creating the task: MCP Error" in result

async def test_query_reminder_tasks_with_tasks(mock_managers):
    """Verify querying tasks when tasks exist."""
    mock_tool_manager, _ = mock_managers
    mock_tasks = [
        Task(id="1", title="Task 1", priority=TaskPriority.HIGH, due_date=date(2025, 1, 1)),
        Task(id="2", title="Task 2", priority=TaskPriority.MEDIUM)
    ]
    mock_tool_manager.reminders_tool.get_reminders = AsyncMock(return_value=mock_tasks)

    result = await query_reminder_tasks()

    assert "You have 2 pending task(s)" in result
    assert "Task 1 (Due: 2025-01-01) [HIGH] [ID: 1]" in result
    assert "Task 2 [ID: 2]" in result

async def test_query_reminder_tasks_no_tasks(mock_managers):
    """Verify querying tasks when no tasks exist."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.get_reminders = AsyncMock(return_value=[])

    result = await query_reminder_tasks()

    assert "✅ You have no pending tasks." in result

async def test_complete_reminder_task_success(mock_managers):
    """Verify successful completion of a task."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.complete_reminder = AsyncMock(return_value=True)
    
    result = await complete_reminder_task(task_id="task_123")
    
    assert "✅ Task marked as completed." in result
    mock_tool_manager.reminders_tool.complete_reminder.assert_called_with("task_123")

async def test_complete_reminder_task_not_found(mock_managers):
    """Verify handling of a non-existent task for completion."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.complete_reminder = AsyncMock(return_value=False)
    
    result = await complete_reminder_task(task_id="task_999")
    
    assert "❌ Could not find or complete task with ID: task_999." in result

async def test_delete_reminder_task_success(mock_managers):
    """Verify successful deletion of a task."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.delete_reminder = AsyncMock(return_value=True)
    
    result = await delete_reminder_task(task_id="task_123")
    
    assert "✅ Task successfully deleted." in result
    mock_tool_manager.reminders_tool.delete_reminder.assert_called_with("task_123")

async def test_update_reminder_task_success(mock_managers):
    """Verify successful update of a task."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.update_reminder = AsyncMock(return_value=True)
    
    result = await update_reminder_task(task_id="task_123", new_title="Updated Title")
    
    assert "✅ Task ID task_123 updated successfully." in result
    mock_tool_manager.reminders_tool.update_reminder.assert_called_with("task_123", {"title": "Updated Title"})

async def test_update_reminder_task_no_changes(mock_managers):
    """Verify that update does not proceed if no new data is provided."""
    mock_tool_manager, _ = mock_managers
    result = await update_reminder_task(task_id="task_123")
    assert "⚠️ No update information provided." in result
    mock_tool_manager.reminders_tool.update_reminder.assert_not_called()

async def test_recommend_next_task_with_tasks(mock_managers):
    """Verify task recommendation when tasks are available."""
    mock_tool_manager, mock_llm_manager = mock_managers
    mock_tasks = [Task(id="1", title="Crucial Task", priority=TaskPriority.URGENT)]
    mock_tool_manager.reminders_tool.get_reminders = AsyncMock(return_value=mock_tasks)
    mock_llm_manager.client.ainvoke = AsyncMock(return_value=MagicMock(content="Do the Crucial Task because it is urgent."))
    
    result = await recommend_next_task()
    
    assert "💡 **Next Task Recommendation:**" in result
    assert "Do the Crucial Task because it is urgent." in result
    mock_llm_manager.client.ainvoke.assert_called_once()

async def test_recommend_next_task_no_tasks(mock_managers):
    """Verify task recommendation when no tasks exist."""
    mock_tool_manager, _ = mock_managers
    mock_tool_manager.reminders_tool.get_reminders = AsyncMock(return_value=[])
    
    result = await recommend_next_task()
    
    assert "✅ You have no pending tasks. Great job!" in result

async def test_analyze_task_workload_with_tasks(mock_managers):
    """Verify workload analysis when tasks are available."""
    mock_tool_manager, mock_llm_manager = mock_managers
    mock_tasks = [Task(id="1", title="Some Task", priority=TaskPriority.MEDIUM)]
    mock_tool_manager.reminders_tool.get_reminders = AsyncMock(return_value=mock_tasks)
    mock_llm_manager.client.ainvoke = AsyncMock(return_value=MagicMock(content="Your workload is manageable."))
    
    result = await analyze_task_workload()
    
    assert "📊 **Task Workload Analysis:**" in result
    assert "Your workload is manageable." in result
    mock_llm_manager.client.ainvoke.assert_called_once()
