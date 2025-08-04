"""Tools for interacting with a user's calendar."""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Union, Any
import pytz
from tzlocal import get_localzone

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ConfigDict, field_validator
from langchain_core.messages import SystemMessage, HumanMessage

from src.tools import MCPToolManager
from src.state.schemas import Event
from src.utils.llm_manager import LLMManager

# --- Constants ---

DATE_PARSING_PROMPT_TEMPLATE = """
You are an expert date parsing assistant. Your task is to analyze the user's query and
determine a precise start and end date for a calendar query.
Today's date is {current_date}.
You MUST respond with a JSON object containing 'start_date' and 'end_date' fields in 'YYYY-MM-DD' format.
"""

# --- Timezone Handling ---
local_tz = get_localzone()
utc_tz = pytz.utc

# --- Module-level Managers ---

mcp_tools: Optional[MCPToolManager] = None
llm_manager_instance: Optional[LLMManager] = None

def initialize_tools(tool_manager: MCPToolManager, llm_manager: LLMManager):
    """Initialize module-level managers. Must be called before using tools."""
    global mcp_tools, llm_manager_instance
    mcp_tools = tool_manager
    llm_manager_instance = llm_manager

# --- Helper Functions ---

def _format_event_time(time_obj: Any, time_format: str) -> str:
    """
    Safely formats a time object into a string, converting from UTC to local time if necessary.
    """
    dt = None
    if isinstance(time_obj, datetime):
        dt = time_obj
    else:
        try:
            # Fallback for non-standard datetime objects
            dt_str = str(time_obj)
            dt = datetime.fromisoformat(dt_str.split('+')[0])
        except (ValueError, TypeError):
            # If all else fails, return the raw string representation
            return str(time_obj)

    # Assume naive datetimes from the tool are UTC, localize and convert to local time
    if dt.tzinfo is None:
        dt = utc_tz.localize(dt).astimezone(local_tz)
    else:
        dt = dt.astimezone(local_tz)

    return dt.strftime(time_format)


async def _check_time_conflicts(start_time: datetime, end_time: datetime) -> List[Event]:
    """Checks for existing events within a given time window."""
    if not mcp_tools:
        return []
    try:
        arguments = {"start_time": start_time, "end_time": end_time}
        return await mcp_tools.call_tool("list_events", arguments)
    except Exception:
        return []

# --- Pydantic Schemas for Tool Inputs ---

class CreateEventInput(BaseModel):
    model_config = ConfigDict(strict=False)
    title: str = Field(..., description="The title of the event.")
    start_time: Union[datetime, str] = Field(..., description="The start time of the event (ISO format or datetime object).")
    end_time: Union[datetime, str] = Field(..., description="The end time of the event (ISO format or datetime object).")
    notes: Optional[str] = Field(None, description="Event notes or description.")
    location: Optional[str] = Field(None, description="The physical or virtual location of the event.")
    calendar_name: Optional[str] = Field(None, description="Name of the calendar for the event.")
    priority: Optional[int] = Field(5, description="Event priority (1-10) for conflict resolution.")

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def _parse_datetime(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return datetime.fromisoformat(v)
        return v

# --- Calendar Tools ---

@tool(args_schema=CreateEventInput)
async def create_calendar_event(
    title: str,
    start_time: Union[datetime, str],
    end_time: Union[datetime, str],
    notes: Optional[str] = None,
    location: Optional[str] = None,
    calendar_name: Optional[str] = None,
    priority: int = 5
) -> str:
    """Creates a new event in the user's calendar."""
    if not mcp_tools:
        return "😅 抱歉，日历系统还没有准备好，请稍后再试～"

    # Parse datetime values directly using the validator
    start_dt = CreateEventInput._parse_datetime(start_time)
    end_dt = CreateEventInput._parse_datetime(end_time)

    try:
        conflicts = await _check_time_conflicts(start_dt, end_dt)
        if conflicts:
            if len(conflicts) == 1:
                return f"⚠️ 抱歉，这个时间段已经有安排了：{conflicts[0].title}。请选择其他时间吧～"
            else:
                conflict_titles = "、".join([c.title for c in conflicts])
                return f"⚠️ 抱歉，这个时间段已经有 {len(conflicts)} 个安排：{conflict_titles}。请选择其他时间吧～"

        arguments = {
            "title": title,
            "start_time": start_dt,
            "end_time": end_dt,
            "notes": notes or "",
            "location": location or "",
            "calendar_name": calendar_name or "个人"
        }
        result = await mcp_tools.call_tool("create_event", arguments)
        
        # Verify the event was actually created by checking the result
        if result and hasattr(result, 'identifier'):
            # Format the time for display
            start_time_str = start_dt.strftime('%m月%d日 %H:%M')
            if start_dt.date() == end_dt.date():
                end_time_str = end_dt.strftime('%H:%M')
                time_display = f"{start_time_str}-{end_time_str}"
            else:
                end_time_str = end_dt.strftime('%m月%d日 %H:%M')
                time_display = f"{start_time_str} - {end_time_str}"
            
            return f"✅ 好的！已经为您安排了「{title}」，时间是 {time_display}。"
        else:
            return f"⚠️ 事件创建可能有问题，请检查日历确认。"
    except Exception as e:
        return f"❌ 抱歉，创建日程时出现了问题：{e}"


@tool
async def query_calendar_events(user_query: str, calendar_name: Optional[str] = None) -> str:
    """Retrieves and lists events from the user's calendar based on a natural language query for a date or date range."""
    if not mcp_tools or not llm_manager_instance:
        return "😅 抱歉，日历系统还没有准备好，请稍后再试～"

    try:
        system_prompt = DATE_PARSING_PROMPT_TEMPLATE.format(current_date=date.today().isoformat())
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]
        response = await llm_manager_instance.client.ainvoke(messages, response_format={"type": "json_object"})
        date_data = json.loads(response.content)

        start_date_obj = datetime.fromisoformat(date_data['start_date']).date()
        end_date_obj = datetime.fromisoformat(date_data['end_date']).date()

        start_time = datetime.combine(start_date_obj, datetime.min.time())
        end_time = datetime.combine(end_date_obj, datetime.max.time())

        events: List[Event] = await _check_time_conflicts(start_time, end_time)

        start_str = start_date_obj.strftime('%Y年%m月%d日')
        end_str = end_date_obj.strftime('%Y年%m月%d日')

        if not events:
            if start_str == end_str:
                return f"📅 {start_str} 这一天您暂时没有安排任何日程，可以好好休息一下～"
            else:
                return f"📅 从 {start_str} 到 {end_str}，您暂时没有安排任何日程呢～"

        event_lines = []
        for event in events:
            # Now uses the timezone-aware formatting function
            start = _format_event_time(event.start_time, '%H:%M')
            end = _format_event_time(event.end_time, '%H:%M')
            
            # Add location info if available
            location_info = f" @ {event.location}" if event.location else ""
            event_lines.append(f"  🔹 **{event.title}** ({start} - {end}){location_info}")

        result_str = "\n".join(event_lines)
        if start_str == end_str:
            return f"📅 **{start_str} 的日程安排：**\n{result_str}"
        else:
            return f"📅 **从 {start_str} 到 {end_str} 的日程安排：**\n{result_str}"

    except Exception as e:
        return f"😅 抱歉，查询日程时出现了一些问题，请稍后再试～"


@tool
async def update_calendar_event(event_id: str, title: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, notes: Optional[str] = None, location: Optional[str] = None) -> str:
    """Modifies an existing calendar event."""
    if not mcp_tools:
        return "😅 抱歉，日历系统还没有准备好，请稍后再试～"
    try:
        update_fields = {
            "title": title, "start_time": start_time, "end_time": end_time,
            "notes": notes, "location": location
        }
        update_request = {k: v for k, v in update_fields.items() if v is not None}

        if not update_request:
            return "🤔 请告诉我您想要修改什么内容呢？比如标题、时间或者地点～"

        arguments = {"event_id": event_id, "request": update_request}
        updated_event = await mcp_tools.call_tool("update_event", arguments)
        return f"✅ 好的！已经帮您更新了「{updated_event.title}」的信息～"
    except Exception as e:
        return f"😅 抱歉，更新日程时出现了一些问题，请稍后再试～"


@tool
async def delete_calendar_event(event_name: str) -> str:
    """Permanently deletes an event from the calendar based on event name."""
    if not mcp_tools or not llm_manager_instance:
        return "😅 抱歉，日历系统还没有准备好，请稍后再试～"
    
    try:
        # 获取未来30天的事件列表
        start_dt = datetime.combine(date.today(), datetime.min.time())
        end_dt = datetime.combine(date.today() + timedelta(days=30), datetime.max.time())
        
        all_events = await _check_time_conflicts(start_dt, end_dt)
        
        if not all_events:
            return "📅 在接下来的30天内没有找到任何日程呢～"
        
        # 筛选包含事件名称的事件
        matches = [
            event for event in all_events
            if event.title and event_name.lower() in event.title.lower()
        ]
        
        if not matches:
            return f"🔍 没有找到包含「{event_name}」的日程，请检查事件名称是否正确～"
        
        # 如果只有一个匹配项，直接删除
        if len(matches) == 1:
            event_to_delete = matches[0]
            if not event_to_delete.identifier:
                return f"😅 抱歉，无法获取「{event_to_delete.title}」的事件ID，请稍后再试～"
            arguments = {"event_id": event_to_delete.identifier}
            result = await mcp_tools.call_tool("delete_event", arguments)
            if "Successfully deleted" in result:
                return f"✅ 好的！已经帮您删除了「{event_to_delete.title}」这个日程～"
            else:
                return f"😅 抱歉，删除日程时遇到了问题：{result}"
        
        # 如果有多个匹配项，使用LLM来决定删除哪个
        event_list = []
        for i, event in enumerate(matches, 1):
            start_str = _format_event_time(event.start_time, '%m-%d %H:%M')
            end_str = _format_event_time(event.end_time, '%H:%M')
            location_info = f" @ {event.location}" if event.location else ""
            event_list.append(f"{i}. {event.title} ({start_str} - {end_str}){location_info}")
        
        event_list_text = "\n".join(event_list)
        
        # 使用LLM来决定删除哪个事件
        system_prompt = """你是一个智能助手，帮助用户从多个相似的事件中选择要删除的一个。
请仔细分析用户提供的事件名称和候选事件列表，选择最符合用户意图的事件。
你必须只返回一个数字（对应事件列表中的编号），不要包含任何其他文字。"""
        
        user_prompt = f"""用户想要删除包含「{event_name}」的事件，找到了以下{len(matches)}个候选事件：

{event_list_text}

请根据事件名称的匹配程度和时间安排，选择最符合用户意图的事件。只返回对应的数字编号。"""
        
        llm_response = await llm_manager_instance.invoke(user_prompt, system_prompt)
        
        try:
            selected_index = int(llm_response.strip()) - 1
            if 0 <= selected_index < len(matches):
                event_to_delete = matches[selected_index]
                if not event_to_delete.identifier:
                    return f"😅 抱歉，无法获取「{event_to_delete.title}」的事件ID，请稍后再试～"
                arguments = {"event_id": event_to_delete.identifier}
                result = await mcp_tools.call_tool("delete_event", arguments)
                if "Successfully deleted" in result:
                    return f"✅ 好的！已经帮您删除了「{event_to_delete.title}」这个日程～"
                else:
                    return f"😅 抱歉，删除日程时遇到了问题：{result}"
            else:
                return "😅 抱歉，选择的事件编号无效，请重新尝试～"
        except ValueError:
            return "😅 抱歉，无法解析选择的事件，请重新尝试～"
            
    except Exception as e:
        return f"😅 抱歉，删除日程时出现了一些问题：{str(e)}"


@tool
async def fuzzy_search_events(search_term: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> str:
    """Searches for events by a keyword or partial name within a date range."""
    if not mcp_tools:
        return "😅 抱歉，日历系统还没有准备好，请稍后再试～"
    try:
        start_dt = datetime.combine(start_date or date.today(), datetime.min.time())
        end_dt = datetime.combine(end_date or (start_dt.date() + timedelta(days=30)), datetime.max.time())

        all_events = await _check_time_conflicts(start_dt, end_dt)

        if not all_events:
            return "📅 在指定的时间范围内没有找到任何日程呢～"

        matches = [
            event for event in all_events
            if event.title and search_term.lower() in event.title.lower()
        ]

        if not matches:
            return f"🔍 没有找到包含「{search_term}」的日程，试试其他关键词吧～"

        if len(matches) == 1:
            response_lines = [f"🔍 找到了 1 个包含「{search_term}」的日程："]
        else:
            response_lines = [f"🔍 找到了 {len(matches)} 个包含「{search_term}」的日程："]
            
        for event in matches:
            start_str = _format_event_time(event.start_time, '%m-%d %H:%M')
            end_str = _format_event_time(event.end_time, '%H:%M')
            location_info = f" @ {event.location}" if event.location else ""
            response_lines.append(f"  🔹 **{event.title}** ({start_str} - {end_str}){location_info}")

        return "\n".join(response_lines)
    except Exception as e:
        return f"😅 抱歉，搜索日程时出现了一些问题，请稍后再试～"

# --- Tool List ---

calendar_tools_list = [
    create_calendar_event,
    query_calendar_events,
    update_calendar_event,
    delete_calendar_event,
    fuzzy_search_events,
]
