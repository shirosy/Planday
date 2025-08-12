"""Tools for interacting with a user's to-do lists and reminders."""

from datetime import date
from typing import Optional, List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools import MCPToolManager
from src.state.schemas import Task, TaskPriority, TaskStatus
from src.utils.llm_manager import LLMManager

# --- Module-level Managers ---
mcp_tools: Optional[MCPToolManager] = None
llm_manager_instance: Optional[LLMManager] = None

def initialize_tools(tool_manager: MCPToolManager, llm_manager: LLMManager):
    """Initialize module-level managers. Must be called before using tools."""
    global mcp_tools, llm_manager_instance
    mcp_tools = tool_manager
    llm_manager_instance = llm_manager
    return task_tools_list

# --- Pydantic Schemas for Tool Inputs ---

class CreateTaskInput(BaseModel):
    title: str = Field(..., description="The title of the task or reminder.")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="The priority of the task.")
    due_date: Optional[date] = Field(None, description="The due date for the task in YYYY-MM-DD format.")
    description: Optional[str] = Field(None, description="A detailed description for the task.")

class UpdateTaskInput(BaseModel):
    task_id: str = Field(..., description="The unique ID of the task to update.")
    new_title: Optional[str] = Field(None, description="The new title for the task.")
    new_priority: Optional[TaskPriority] = Field(None, description="The new priority for the task.")
    new_due_date: Optional[date] = Field(None, description="The new due date for the task.")
    new_description: Optional[str] = Field(None, description="The new description for the task.")

# --- Task-related Tools ---

@tool(args_schema=CreateTaskInput)
async def create_reminder_task(title: str, priority: TaskPriority = TaskPriority.MEDIUM, due_date: Optional[date] = None, description: Optional[str] = None) -> str:
    """
    <tool_name>create_reminder_task</tool_name>
    <description>
    Creates a new personal task, to-do item, or reminder. Use for tasks that don't have a specific start/end time.
    </description>
    <parameters>
        <parameter name="title">The title of the task.</parameter>
        <parameter name="priority">Optional. Priority can be 'low', 'medium', 'high', or 'urgent'. Defaults to 'medium'.</parameter>
        <parameter name="due_date">Optional. Due date in 'YYYY-MM-DD' format.</parameter>
        <parameter name="description">Optional. A detailed description of the task.</parameter>
    </parameters>
    <example>
    User: "Remind me to pick up the dry cleaning by this Friday. It's high priority."
    </example>
    """
    if not mcp_tools:
        return "❌ Error: Task tool manager not initialized."
    try:
        task_data = Task(title=title, priority=priority, due_date=due_date, description=description)
        task_id = await mcp_tools.reminders_tool.create_reminder(task_data)
        return f"✅ Task '{title}' created successfully with ID: {task_id}."
    except Exception as e:
        return f"❌ An error occurred while creating the task: {e}"

@tool
async def query_reminder_tasks() -> str:
    """
    <tool_name>query_reminder_tasks</tool_name>
    <description>
    Retrieves and lists all pending tasks and reminders. Use to answer "What are my tasks?" or "Show me my to-do list."
    </description>
    <parameters></parameters>
    <example>
    User: "What's on my to-do list?"
    </example>
    """
    if not mcp_tools:
        return "❌ Error: Task tool manager not initialized."
    try:
        tasks: List[Task] = await mcp_tools.reminders_tool.get_reminders()
        if not tasks:
            return "✅ You have no pending tasks."
        
        response_lines = [f"📋 You have {len(tasks)} pending task(s):"]
        for task in tasks:
            due_str = f" (Due: {task.due_date})" if task.due_date else ""
            prio_str = f" [{task.priority.value.upper()}]" if task.priority != TaskPriority.MEDIUM else ""
            response_lines.append(f"  - {task.title}{due_str}{prio_str} [ID: {task.id}]")
        
        return "\n".join(response_lines)
    except Exception as e:
        return f"❌ An error occurred while querying tasks: {e}"

@tool
async def complete_reminder_task(task_id: str) -> str:
    """
    <tool_name>complete_reminder_task</tool_name>
    <description>
    Marks a specific task as 'completed' or 'done' using its unique ID or title.
    The AI should use the exact task title or ID from the task list.
    </description>
    <parameters>
        <parameter name="task_id">The unique ID or exact title of the task to mark as complete.</parameter>
    </parameters>
    <example>
    User: "I've finished the 'Prepare presentation slides' task." 
    AI should first call query_reminder_tasks to get the task list, then use the exact title.
    </example>
    """
    if not mcp_tools:
        return "❌ Error: Task tool manager not initialized."
    try:
        success = await mcp_tools.reminders_tool.complete_reminder(task_id)
        if success:
            return f"✅ Task '{task_id}' has been marked as completed."
        else:
            return f"❌ Could not find or complete task: '{task_id}'. Please check the task title or ID."
    except Exception as e:
        return f"❌ An error occurred while completing the task: {e}"

@tool
async def delete_reminder_task(task_id: str) -> str:
    """
    <tool_name>delete_reminder_task</tool_name>
    <description>
    Permanently deletes a task using its unique ID or exact title.
    When user refers to position (like "first task" or "第一个"), AI should first query tasks to get the exact title.
    </description>
    <parameters>
        <parameter name="task_id">The unique ID or exact title of the task to delete.</parameter>
    </parameters>
    <example>
    User: "Delete the first task" -> AI should first call query_reminder_tasks, then delete using exact title
    User: "Delete 'Clean garage' task" -> AI can directly use the exact title
    </example>
    """
    if not mcp_tools:
        return "❌ Error: Task tool manager not initialized."
    try:
        success = await mcp_tools.reminders_tool.delete_reminder(task_id)
        if success:
            return f"✅ Task '{task_id}' has been successfully deleted."
        else:
            return f"❌ Could not find or delete task: '{task_id}'. Please check the task title or ID."
    except Exception as e:
        return f"❌ An error occurred while deleting the task: {e}"

@tool(args_schema=UpdateTaskInput)
async def update_reminder_task(task_id: str, new_title: Optional[str] = None, new_priority: Optional[TaskPriority] = None, new_due_date: Optional[date] = None, new_description: Optional[str] = None) -> str:
    """
    <tool_name>update_reminder_task</tool_name>
    <description>
    Modifies an existing task's details using its unique ID.
    </description>
    <parameters>
        <parameter name="task_id">The unique ID of the task to update.</parameter>
        <parameter name="new_title">Optional. The new title for the task.</parameter>
        <parameter name="new_priority">Optional. The new priority: 'low', 'medium', 'high', 'urgent'.</parameter>
        <parameter name="new_due_date">Optional. The new due date in 'YYYY-MM-DD' format.</parameter>
        <parameter name="new_description">Optional. The new description for the task.</parameter>
    </parameters>
    <example>
    User: "Change the due date for my 'Submit report' task to this Friday." (Requires first finding the task ID).
    </example>
    """
    if not mcp_tools:
        return "❌ Error: Task tool manager not initialized."
    try:
        update_data = {
            "title": new_title, "priority": new_priority, 
            "due_date": new_due_date, "description": new_description
        }
        # Filter out None values to only update provided fields
        update_request = {k: v for k, v in update_data.items() if v is not None}

        if not update_request:
            return "⚠️ No update information provided. Please specify what to change."
            
        success = await mcp_tools.reminders_tool.update_reminder(task_id, update_request)
        return f"✅ Task ID {task_id} updated successfully." if success else f"❌ Failed to update task with ID: {task_id}."
    except Exception as e:
        return f"❌ An error occurred while updating the task: {e}"

@tool
async def recommend_next_task() -> str:
    """
    <tool_name>recommend_next_task</tool_name>
    <description>
    Analyzes all pending tasks and recommends the most important one to focus on next. Use when the user asks for recommendations like "What should I do now?".
    </description>
    <parameters></parameters>
    <example>
    User: "What should I focus on today?"
    </example>
    """
    if not mcp_tools or not llm_manager_instance:
        return "❌ Error: Tool managers not initialized."
    try:
        tasks: List[Task] = await mcp_tools.reminders_tool.get_reminders()
        if not tasks:
            return "✅ You have no pending tasks. Great job!"

        task_list_str = "\n".join(
            [f"- Title: {t.title}, Due: {t.due_date}, Priority: {t.priority.value}, Description: {t.description}" for t in tasks]
        )

        prompt = f"""
        Given the following list of tasks, which single task is the most important to do next?
        Consider due dates (today is {date.today()}) and priority levels.
        Provide a brief reason for your choice.

        Tasks:
        {task_list_str}

        Respond with the title of the recommended task and a short justification.
        """
        response = await llm_manager_instance.client.ainvoke(prompt)
        return f"💡 **Next Task Recommendation:**\n{response.content}"
    except Exception as e:
        return f"❌ An error occurred while recommending a task: {e}"

@tool
async def analyze_task_workload() -> str:
    """
    <tool_name>analyze_task_workload</tool_name>
    <description>
    Provides a high-level analysis of the user's task workload, including statistics and a qualitative assessment. Use for questions like "How am I doing with my tasks?".
    </description>
    <parameters></parameters>
    <example>
    User: "Give me a summary of my workload."
    </example>
    """
    if not mcp_tools or not llm_manager_instance:
        return "❌ Error: Tool managers not initialized."
    try:
        tasks: List[Task] = await mcp_tools.reminders_tool.get_reminders()
        if not tasks:
            return "📊 You have no tasks to analyze. Looks like you're all caught up!"

        task_list_str = "\n".join(
            [f"- Title: {t.title}, Due: {t.due_date}, Priority: {t.priority.value}, Status: {t.status.value}" for t in tasks]
        )

        prompt = f"""
        Analyze the following list of tasks and provide a concise workload analysis.
        Today's date is {date.today()}.

        Tasks:
        {task_list_str}

        Your analysis should include:
        1. A count of overdue tasks.
        2. A count of tasks due today.
        3. A brief, qualitative assessment of the workload (e.g., Light, Manageable, Heavy).
        4. A key recommendation or insight.
        """
        response = await llm_manager_instance.client.ainvoke(prompt)
        return f"📊 **Task Workload Analysis:**\n{response.content}"
    except Exception as e:
        return f"❌ An error occurred while analyzing tasks: {e}"

# --- Tool List ---
task_tools_list = [
    create_reminder_task, 
    query_reminder_tasks, 
    complete_reminder_task, 
    delete_reminder_task,
    update_reminder_task,
    recommend_next_task,
    analyze_task_workload
]
