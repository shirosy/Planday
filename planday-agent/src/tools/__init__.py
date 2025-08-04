"""Enhanced MCP tool integration for new agent architecture."""

import asyncio
import json
import subprocess
import os
import sys
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import structlog
from concurrent.futures import Executor

from src.state.schemas import CalendarEvent, Task, TaskPriority, TaskStatus, EventType, Event

logger = structlog.get_logger()

# NOTE: The contents of this __init__.py file are a mix of tool definitions
# and the necessary imports to expose the tools to the graph factory.
# This structure has evolved and could be refactored for better separation of concerns.

class MCPToolError(Exception):
    """Custom exception for MCP tool operations."""
    pass


class CalendarTool(BaseTool):
    """Tool for interacting with macOS Calendar via MCP."""
    
    name: str = "calendar_tool"
    description: str = "Interact with macOS Calendar application through MCP."
    
    mcp_server_path: str = Field(description="Path to the iCal MCP server")
    executor: Executor = Field(description="The executor for running sync code in async.")
    
    def __init__(self, mcp_server_path: str, executor: Executor, **kwargs):
        super().__init__(mcp_server_path=mcp_server_path, executor=executor, **kwargs)
    
    async def _run_mcp_command(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        loop = asyncio.get_running_loop()
        try:
            mcp_ical_src = os.path.join(self.mcp_server_path, "src")
            
            if mcp_ical_src not in sys.path:
                sys.path.insert(0, mcp_ical_src)
                logger.info(f"Added mcp_ical path to sys.path: {mcp_ical_src}")
            
            from mcp_ical.ical import CalendarManager
            from mcp_ical.models import CreateEventRequest, UpdateEventRequest

            manager = await loop.run_in_executor(self.executor, CalendarManager)
            
            if tool_name == "create_event":
                request = CreateEventRequest(
                    title=arguments["title"],
                    start_time=arguments["start_time"],
                    end_time=arguments["end_time"],
                    notes=arguments.get("notes", ""),
                    location=arguments.get("location", ""),
                    calendar_name=arguments.get("calendar_name", "个人")
                )
                return await loop.run_in_executor(self.executor, manager.create_event, request)
            
            elif tool_name == "list_events":
                return await loop.run_in_executor(
                    self.executor,
                    manager.list_events,
                    arguments["start_time"],
                    arguments["end_time"],
                    arguments.get("calendar_name")
                )

            elif tool_name == "update_event":
                update_data = UpdateEventRequest(**arguments['request'])
                return await loop.run_in_executor(
                    self.executor,
                    manager.update_event,
                    arguments['event_id'],
                    update_data
                )

            elif tool_name == "delete_event":
                success = await loop.run_in_executor(self.executor, manager.delete_event, arguments['event_id'])
                if success:
                    return f"Successfully deleted event with ID: {arguments['event_id']}"
                else:
                    return f"Failed to delete event. Event with ID {arguments['event_id']} not found or delete failed."

            else:
                raise ValueError(f"Unknown calendar tool: {tool_name}")
        
        except Exception as e:
            logger.error("MCP calendar command failed", error=str(e), tool=tool_name, exc_info=True)
            raise MCPToolError(f"❌ MCP command execution failed for {tool_name}: {e}")

    def _run(self, query: str) -> str:
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> Any:
        # This is a stub for direct langchain tool usage, not used by our agent
        return "This tool is not meant to be run directly with a string query."


class RemindersTool(BaseTool):
    """Tool for interacting with macOS Reminders via MCP."""
    
    name: str = "reminders_tool"
    description: str = "Interact with macOS Reminders application through MCP."
    
    mcp_server_path: str = Field(description="Path to the Reminders MCP server")
    
    def __init__(self, mcp_server_path: str, **kwargs):
        super().__init__(mcp_server_path=mcp_server_path, **kwargs)

    async def _run_mcp_command(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP command via stdio with Apple Reminders MCP server."""
        try:
            if not os.path.exists(self.mcp_server_path):
                raise FileNotFoundError(f"❌ Reminders MCP server not found at: {self.mcp_server_path}")
            
            init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            tool_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}
            
            cmd = ["node", self.mcp_server_path]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            input_data = json.dumps(init_request) + "\n" + json.dumps(tool_request) + "\n"
            stdout, stderr = await process.communicate(input=input_data.encode())
            
            if process.returncode != 0:
                raise MCPToolError(f"MCP server failed. stderr: {stderr.decode()}")
            
            lines = [line for line in stdout.decode().strip().split('\n') if line.strip() and not line.startswith('Apple Reminders')]
            if len(lines) < 2:
                raise MCPToolError(f"Expected 2 responses, got {len(lines)}. stdout: {stdout.decode()}")
            
            tool_response = json.loads(lines[1])
            if "error" in tool_response:
                raise MCPToolError(f"MCP server error: {tool_response['error']}")
            
            # Extract the actual result from MCP response format
            result = tool_response.get("result", {})
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                content = result["content"][0]
                if content.get("type") == "text" and "text" in content:
                    # Parse the JSON string inside the text field
                    return json.loads(content["text"])
            
            return result
        
        except Exception as e:
            logger.error("Reminders MCP command failed", error=str(e), tool=tool_name, exc_info=True)
            raise MCPToolError(f"❌ Reminders MCP command execution failed for {tool_name}: {e}")

    def _run(self, query: str) -> str:
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> Any:
        return "This tool is not meant to be run directly with a string query."
    
    async def create_reminder(self, task: 'Task') -> str:
        """Create a new reminder/task."""
        arguments = {
            "listName": "Reminders",  # Default list name - only Reminders list exists
            "title": task.title,
            "notes": task.description or ""
        }
        # Only add dueDate if it exists (MCP server doesn't accept null)
        if task.due_date:
            arguments["dueDate"] = task.due_date.isoformat()
        result = await self._run_mcp_command("createReminder", arguments)
        # MCP server returns success boolean, we return the task title as ID
        if result.get("success", False):
            return task.title
        return ""
    
    async def get_reminders(self) -> List['Task']:
        """Get all pending reminders/tasks."""
        arguments = {"listName": "Reminders"}
        result = await self._run_mcp_command("getReminders", arguments)
        
        from src.state.schemas import Task, TaskPriority, TaskStatus
        tasks = []
        for reminder in result.get("reminders", []):
            # Parse due_date if present
            due_date = None
            if reminder.get("dueDate"):
                try:
                    due_date = datetime.fromisoformat(reminder["dueDate"]).date()
                except (ValueError, TypeError):
                    # If parsing fails, leave due_date as None
                    pass
            
            task = Task(
                id=reminder.get("name"),  # Use name as ID since MCP uses reminderName
                title=reminder.get("name", ""),  # name is the title in MCP
                description=reminder.get("notes", ""),
                priority=TaskPriority.MEDIUM,  # Default since Apple Reminders doesn't have priority
                status=TaskStatus.COMPLETED if reminder.get("completed", False) else TaskStatus.PENDING,
                due_date=due_date
            )
            # Only include non-completed tasks
            if not reminder.get("completed", False):
                tasks.append(task)
        return tasks
    
    async def complete_reminder(self, task_id: str) -> bool:
        """Mark a reminder/task as completed."""
        arguments = {
            "listName": "Reminders",
            "reminderName": task_id  # task_id is actually the task title/name
        }
        try:
            result = await self._run_mcp_command("completeReminder", arguments)
            return result.get("success", False)
        except Exception:
            return False
    
    async def delete_reminder(self, task_id: str) -> bool:
        """Delete a reminder/task."""
        arguments = {
            "listName": "Reminders",
            "reminderName": task_id  # task_id is actually the task title/name
        }
        try:
            result = await self._run_mcp_command("deleteReminder", arguments)
            return result.get("success", False)
        except Exception:
            return False
    
    async def update_reminder(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a reminder/task by recreating it."""
        # Since MCP server doesn't expose update functionality,
        # we simulate it by recreating the task
        try:
            # First, get the current task details by querying all tasks
            tasks = await self.get_reminders()
            current_task = None
            for task in tasks:
                if task.id == task_id:
                    current_task = task
                    break
            
            if not current_task:
                return False  # Task not found
            
            # Delete the old task
            delete_success = await self.delete_reminder(task_id)
            if not delete_success:
                return False
            
            # Create updated task with new data
            from src.state.schemas import Task
            updated_task = Task(
                title=update_data.get("title", current_task.title),
                description=update_data.get("description", current_task.description),
                priority=update_data.get("priority", current_task.priority),
                due_date=update_data.get("due_date", current_task.due_date)
            )
            
            # Create the new task
            new_id = await self.create_reminder(updated_task)
            return bool(new_id)
            
        except Exception:
            return False


class MCPToolManager:
    """Manager for MCP tool operations."""
    
    def __init__(self, calendar_server_path: str, reminders_server_path: str, executor: Executor):
        self.calendar_tool = CalendarTool(mcp_server_path=calendar_server_path, executor=executor)
        self.reminders_tool = RemindersTool(mcp_server_path=reminders_server_path)
        
        # Note: Tool initialization happens in GraphFactory where LLMManager is available
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific MCP tool by name."""
        try:
            if tool_name in ["create_event", "list_events", "update_event", "delete_event"]:
                return await self.calendar_tool._run_mcp_command(tool_name, arguments)
            elif tool_name in ["createReminder", "getReminders", "updateReminder", "deleteReminder", "completeReminder"]:
                return await self.reminders_tool._run_mcp_command(tool_name, arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e), exc_info=True)
            raise


# ==============================================================================
# EXPOSE TOOLS AND INITIALIZERS TO THE PACKAGE LEVEL
# ==============================================================================
# This is the crucial part that makes the tools available for import in graph_factory.py

from .calendar_tools import (
    calendar_tools_list,
    initialize_tools as initialize_calendar_tools,
)
from .task_tools import (
    task_tools_list,
    initialize_tools as initialize_task_tools,
)
from .planning_tools import (
    planning_tools_list,
    initialize_planner,
)
from .parser_tools import (
    parser_tools_list,
    initialize_parser,
)

__all__ = [
    "MCPToolManager",
    "calendar_tools_list",
    "initialize_calendar_tools",
    "task_tools_list",
    "initialize_task_tools",
    "planning_tools_list",
    "initialize_planner",
    "parser_tools_list",
    "initialize_parser",
]
