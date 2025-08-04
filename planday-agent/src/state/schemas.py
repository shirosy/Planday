"""Pydantic models and TypedDict schemas for PlanDay agent state."""

from datetime import datetime, date
from enum import Enum
from typing import TypedDict, List, Any, Optional, Annotated

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

# --- Enums for Data Models ---

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EventType(str, Enum):
    """Calendar event types."""
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    DEADLINE = "deadline"
    PERSONAL = "personal"
    WORK = "work"

# --- Pydantic Data Models (for Tools) ---

class Event(BaseModel):
    """A generic event model, compatible with the output of mcp-ical."""
    identifier: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    raw_event: Optional[Any] = None

class CalendarEvent(BaseModel):
    """Calendar event model, used for structured tool inputs/outputs."""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    event_type: EventType = EventType.PERSONAL
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Task(BaseModel):
    """Task/reminder model, used for structured tool inputs/outputs."""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[date] = None
    estimated_duration_minutes: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    subtasks: List["Task"] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

Task.model_rebuild()

# --- LangGraph State Schema ---

class GlobalState(TypedDict):
    """
    The complete, unified state for the LangGraph.
    'messages' is annotated with add_messages to ensure that new messages are
    always appended to the list, maintaining the conversation history.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    route_decision: Optional[str]
    user_context: Optional[dict]  # User preferences, timezone, etc.
    conversation_summary: Optional[str]  # Summary of long conversations
    last_activity: Optional[datetime]  # Track conversation activity
    message_count: Optional[int]  # Track message count for optimization
