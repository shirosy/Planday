
"""
Simple and Practical Planning Tools for PlanDay Agent System

Focus on reliability and usability over complexity.
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.state.schemas import Task, TaskPriority, TaskStatus
from src.utils.llm_manager import LLMManager
from src.tools import MCPToolManager

# Module-level instances
llm_manager_instance: Optional[LLMManager] = None
mcp_tools_instance: Optional[MCPToolManager] = None

def initialize_planner(llm_manager: LLMManager, mcp_tools: Optional[MCPToolManager] = None):
    """Initialize the planning tools with required managers."""
    global llm_manager_instance, mcp_tools_instance
    llm_manager_instance = llm_manager
    mcp_tools_instance = mcp_tools


class DecomposeTaskInput(BaseModel):
    user_request: str = Field(description="The user's high-level goal or complex task that needs to be decomposed.")

@tool(args_schema=DecomposeTaskInput)
async def decompose_task_into_steps(user_request: str) -> str:
    """
    <tool_name>decompose_task_into_steps</tool_name>
    <description>
    Use this tool when a user presents a complex goal or project and needs help breaking it down into smaller, manageable steps. This tool is ideal for high-level planning and turning a large idea into an actionable to-do list.
    </description>
    <parameters>
        <parameter name="user_request">The high-level goal or complex task provided by the user. For example: "plan a marketing campaign" or "launch the new website".</parameter>
    </parameters>
    <example>
    User: "I need to organize a team offsite for next quarter. Can you help me break it down?"
    </example>
    """
    if not llm_manager_instance:
        return "Error: Planner tool not initialized with an LLM Manager."

    try:
        prompt = f"""
        Break down this task into simple, actionable steps: "{user_request}"
        
        Provide 3-7 concrete steps that a person can actually do.
        Make each step specific and clear.
        Don't include vague steps like "plan" or "research" - be specific about what to do.
        
        Format as a numbered list.
        """
        
        response = await llm_manager_instance.invoke(prompt)
        
        return f"I've broken down '{user_request}' into these actionable steps:\n\n{response}\n\nWould you like me to add any of these as tasks to your reminder list?"
        
    except Exception as e:
        return f"An error occurred during task decomposition: {e}"

class ScheduleTaskInput(BaseModel):
    task_name: str = Field(description="Name of the task to schedule")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes (optional)")
    preferred_time: Optional[str] = Field(None, description="Preferred time: morning, afternoon, or evening (optional)")
    days_ahead: Optional[int] = Field(7, description="How many days ahead to look for time slots")

@tool(args_schema=ScheduleTaskInput)
async def suggest_task_time(
    task_name: str, 
    estimated_duration: Optional[int] = None,
    preferred_time: Optional[str] = None,
    days_ahead: int = 7
) -> str:
    """
    <tool_name>suggest_task_time</tool_name>
    <description>
    Use this tool to find and suggest appropriate time slots for a single task. It checks the user's calendar for availability and suggests potential times based on the task's estimated duration and the user's general preferences (e.g., morning, afternoon).
    </description>
    <parameters>
        <parameter name="task_name">The name of the task you want to schedule.</parameter>
        <parameter name="estimated_duration">Optional. The estimated time in minutes required to complete the task. Defaults to 60 minutes.</parameter>
        <parameter name="preferred_time">Optional. A general preference for the time of day, such as 'morning', 'afternoon', or 'evening'.</parameter>
        <parameter name="days_ahead">Optional. How many days into the future to search for available slots. Defaults to 7.</parameter>
    </parameters>
    <example>
    User: "Find me some time to work on the 'Q3 Report'. I think it will take about 2 hours, and I prefer working in the morning."
    </example>
    """
    try:
        # Set defaults
        duration = estimated_duration or 60  # Default 1 hour
        
        # Get current calendar events if available
        calendar_events = []
        if mcp_tools_instance:
            try:
                start_date = date.today()
                end_date = start_date + timedelta(days=days_ahead)
                calendar_events = await mcp_tools_instance.calendar_tool.get_events(start_date, end_date)
            except:
                pass  # Continue without calendar if it fails
        
        # Generate simple suggestions
        suggestions = []
        current_date = date.today()
        
        for i in range(days_ahead):
            check_date = current_date + timedelta(days=i)
            day_name = check_date.strftime("%A, %B %d")
            
            # Skip weekends for work tasks (simple heuristic)
            if check_date.weekday() >= 5 and "work" in task_name.lower():
                continue
            
            # Suggest times based on preference
            if preferred_time == "morning":
                suggested_times = ["09:00", "10:00", "11:00"]
            elif preferred_time == "afternoon":
                suggested_times = ["14:00", "15:00", "16:00"]
            elif preferred_time == "evening":
                suggested_times = ["18:00", "19:00", "20:00"]
            else:
                # Default good times
                suggested_times = ["09:00", "10:00", "14:00", "15:00"]
            
            # Check for conflicts (simplified)
            available_times = []
            for time_str in suggested_times:
                hour = int(time_str.split(":")[0])
                proposed_start = datetime.combine(check_date, datetime.min.time().replace(hour=hour))
                proposed_end = proposed_start + timedelta(minutes=duration)
                
                # Simple conflict check
                has_conflict = False
                for event in calendar_events:
                    if (event.start_time.date() == check_date and 
                        not (proposed_end <= event.start_time or proposed_start >= event.end_time)):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    available_times.append(time_str)
            
            if available_times:
                suggestions.append(f"**{day_name}**: {', '.join(available_times[:2])}")
                
            if len(suggestions) >= 5:  # Limit to 5 suggestions
                break
        
        if not suggestions:
            return f"I couldn't find good available times for '{task_name}' in the next {days_ahead} days. Try extending the search period or checking your calendar manually."
        
        result = f"🕐 **Good times for '{task_name}' ({duration} minutes):**\n\n"
        result += "\n".join(suggestions)
        result += f"\n\n💡 Based on {len(calendar_events)} existing calendar events"
        result += "\n\n**Tips:**\n• Morning (9-11 AM) is great for focused work\n• Afternoon (2-4 PM) works well for meetings\n• Avoid scheduling back-to-back without breaks"
        
        return result
        
    except Exception as e:
        return f"An error occurred while suggesting times: {e}"


class QuickScheduleInput(BaseModel):
    tasks: List[str] = Field(description="List of task names to schedule")
    today_only: Optional[bool] = Field(False, description="Only schedule for today")

@tool(args_schema=QuickScheduleInput)
async def quick_schedule_tasks(tasks: List[str], today_only: bool = False) -> str:
    """
    <tool_name>quick_schedule_tasks</tool_name>
    <description>
    Use this tool to quickly assign a list of tasks to a series of available time slots. It provides a simple, sequential schedule to help the user plan their day or week. This tool is best for users who have multiple tasks and want a straightforward plan without complex optimization.
    </description>
    <parameters>
        <parameter name="tasks">A list of task names to be scheduled.</parameter>
        <parameter name="today_only">Optional. If set to true, the tool will only look for time slots today. Defaults to false.</parameter>
    </parameters>
    <example>
    User: "I have to 'draft email', 'review PR', and 'update ticket'. Can you just lay them out for me for today?"
    </example>
    """
    if not tasks:
        return "No tasks provided to schedule."
    
    try:
        # Simple scheduling logic
        schedule_date = date.today()
        schedule_day = schedule_date.strftime("%A, %B %d")
        
        # Basic time slots (simplified)
        if today_only:
            current_hour = datetime.now().hour
            available_slots = []
            for hour in range(max(current_hour + 1, 9), 18):  # 9 AM to 6 PM
                available_slots.append(f"{hour:02d}:00")
        else:
            available_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        
        # Assign tasks to slots
        scheduled_tasks = []
        for i, task in enumerate(tasks):
            if i < len(available_slots):
                scheduled_tasks.append(f"• **{available_slots[i]}**: {task}")
            else:
                scheduled_tasks.append(f"• **Overflow**: {task} (schedule for next day)")
        
        result = f"📅 **Quick Schedule for {schedule_day}:**\n\n"
        result += "\n".join(scheduled_tasks)
        
        if len(tasks) > len(available_slots):
            result += f"\n\n⚠️ **Note**: You have {len(tasks)} tasks but only {len(available_slots)} good time slots today. Consider spreading some tasks across multiple days."
        
        result += "\n\n💡 **Quick Tips:**\n• Each task gets about 1 hour\n• Take 15-minute breaks between tasks\n• Adjust times based on your energy levels"
        
        return result
        
    except Exception as e:
        return f"An error occurred during quick scheduling: {e}"


class FindFreeTimeInput(BaseModel):
    duration_hours: float = Field(description="How many hours of free time needed")
    days_to_check: Optional[int] = Field(3, description="Number of days ahead to check")

@tool(args_schema=FindFreeTimeInput)
async def find_free_time(duration_hours: float, days_to_check: int = 3) -> str:
    """
    <tool_name>find_free_time</tool_name>
    <description>
    Use this tool to find blocks of free time in the user's calendar that are long enough for a specified activity. It's perfect for when the user asks "When am I free for 2 hours?" or "Find a 90-minute slot for me to do some deep work."
    </description>
    <parameters>
        <parameter name="duration_hours">Required. The duration of the free time block needed, specified in hours (e.g., 1.5 for 90 minutes).</parameter>
        <parameter name="days_to_check">Optional. How many days into the future to search for free time. Defaults to 3 days.</parameter>
    </parameters>
    <example>
    User: "I need to find a 3-hour block sometime in the next couple of days to focus on planning."
    </example>
    """
    try:
        duration_minutes = int(duration_hours * 60)
        
        # Get calendar events if available
        free_blocks = []
        if mcp_tools_instance:
            try:
                start_date = date.today()
                end_date = start_date + timedelta(days=days_to_check)
                events = await mcp_tools_instance.calendar_tool.get_events(start_date, end_date)
                
                # Simple free time detection
                for i in range(days_to_check):
                    check_date = start_date + timedelta(days=i)
                    day_name = check_date.strftime("%A, %B %d")
                    
                    # Check for large free blocks (simplified algorithm)
                    daily_events = [e for e in events if e.start_time.date() == check_date]
                    daily_events.sort(key=lambda x: x.start_time)
                    
                    # Look for gaps
                    work_start = datetime.combine(check_date, datetime.min.time().replace(hour=9))
                    work_end = datetime.combine(check_date, datetime.min.time().replace(hour=18))
                    
                    current_time = work_start
                    for event in daily_events:
                        # Check gap before this event
                        if event.start_time > current_time:
                            gap_minutes = (event.start_time - current_time).total_seconds() / 60
                            if gap_minutes >= duration_minutes:
                                start_str = current_time.strftime("%H:%M")
                                end_str = (current_time + timedelta(hours=duration_hours)).strftime("%H:%M")
                                free_blocks.append(f"**{day_name}**: {start_str} - {end_str}")
                                break
                        current_time = max(event.end_time, current_time)
                    
                    # Check gap after last event
                    if current_time < work_end:
                        gap_minutes = (work_end - current_time).total_seconds() / 60
                        if gap_minutes >= duration_minutes:
                            start_str = current_time.strftime("%H:%M")
                            end_str = (current_time + timedelta(hours=duration_hours)).strftime("%H:%M")
                            free_blocks.append(f"**{day_name}**: {start_str} - {end_str}")
                    
                    if len(free_blocks) >= 5:  # Limit results
                        break
                        
            except:
                # Fallback if calendar fails
                for i in range(days_to_check):
                    check_date = date.today() + timedelta(days=i)
                    day_name = check_date.strftime("%A, %B %d")
                    free_blocks.append(f"**{day_name}**: 09:00 - {(datetime.min + timedelta(hours=9 + duration_hours)).strftime('%H:%M')} (estimated)")
        
        if not free_blocks:
            return f"I couldn't find any {duration_hours}-hour blocks in the next {days_to_check} days. Try reducing the duration or extending the search period."
        
        result = f"🆓 **Available {duration_hours}-hour blocks:**\n\n"
        result += "\n".join(free_blocks[:5])  # Show max 5 results
        result += f"\n\n💡 **Best for {duration_hours} hours:**"
        if duration_hours >= 2:
            result += "\n• Deep work or important projects"
            result += "\n• Turn off notifications for focus"
        else:
            result += "\n• Quick tasks or meetings"
            result += "\n• Good for administrative work"
        
        return result
        
    except Exception as e:
        return f"An error occurred while finding free time: {e}"


# Simple, reliable tool list
planning_tools_list = [
    decompose_task_into_steps,
    suggest_task_time,
    quick_schedule_tasks,
    find_free_time
]
